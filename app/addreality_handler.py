import os
import pathlib
from typing import Optional

import requests
import json

from app import data_classes as dc, utils
import app.log_lib as log_lib


class AddRealityHandler:
    __logger: 'log_lib' = None

    def __init__(self, user: 'dc.User'):
        self.session = requests.session()
        self.data = {'login': user.login, 'password': user.password}
        self.platform_id = user.platform_id

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/83.0.4103.97 Safari/537.36"
        }

    @property
    def logger(self) -> 'log_lib.Logger':
        if self.__logger is None:
            self.__logger = log_lib.get_logger(self.__class__.__name__)
        return self.__logger

    def reload_player(self, device_id: int) -> None:
        """
        Reload the device with an advertising screen
        :param device_id: id of device
        :return: None
        """
        self.logger.info('Reloading player')
        with open('./payload.json') as json_file:
            reload_data = json.load(json_file)
        self.session.put(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/devices/{device_id}',
            headers=self.headers,
            data=json.dumps(reload_data))
        self.logger.info('Player has been reloaded')

    def get_device_info(self, device_id: int):
        r_device_info = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/devices/{device_id}',
            headers=self.headers
        )
        list_of_campaigns_id = []
        device_campaigns = r_device_info.json().get('campaigns', [])
        for device in device_campaigns:
            list_of_campaigns_id.append(device['id'])
        return list_of_campaigns_id

    def get_devices(self) -> list['dc.Device']:
        """
        Get list of devices with id, name and status.
        :return: list['dc.Device']
        """
        self.logger.info("Receiving devices")
        r_existed_devices = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/devices',
            headers=self.headers
        )
        res = [
            dc.Device(
                device['id'],
                device['name']
            ) for device in r_existed_devices.json()['devices'] if device['status'] != 'offline']
        self.logger.info(f"Received devices: {res}")
        return res

    def authorization(self) -> None:
        """
        Authorize user in api.
        :return: None
        """
        self.logger.info(f"Authorizing user...")

        # start authorizing session
        r_start_auth = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/start',
            headers=self.headers,
            data=self.data
        )
        self.data['session_id'] = r_start_auth.json()['session_id']

        # send request with login
        r_post_login = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/check_login',
            headers=self.headers,
            data=json.dumps(self.data)
        )

        # send request with password
        r_post_pass = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/commit_pwd',
            headers=self.headers,
            data=json.dumps(self.data)
        )

        # end authorizing session
        r_end_auth = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/finish',
            headers=self.headers,
            data=json.dumps(self.data)
        )
        self.headers.update({'Referrer Policy': 'strict-origin-when-cross-origin'})

        for resp in [r_post_login, r_post_pass, r_end_auth]:
            if resp.status_code != 200:
                self.logger.critical(f"The user isn't authorized")
        self.logger.info(f"The user is authorized")

    def pause_campaign(self, campaign_id) -> None:
        """
        Pause the advertising campaign.
        :param campaign_id: id of campaign
        :return: None
        """
        pause_ping = {
            'status': 'paused'
        }
        self.session.put(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(pause_ping)
        )
        self.logger.info(f"Campaign {campaign_id} has been paused")

    def start_campaign(self, campaign_id: int) -> None:
        """
        Play the advertising campaign.
        :param campaign_id: id of campaign
        :return: None
        """
        play_ping = {
            'status': 'playing'
        }
        self.session.put(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(play_ping)
        )
        self.logger.info(f"Campaign {campaign_id} has been started")

    def get_content_id(self, file_path: str) -> Optional[int]:
        """
        Get id of media file.
        :param file_path: path to media file on server
        :return: None
        """
        self.logger.info(f"Receiving content from storage...")

        # get filename form file path
        file_name = pathlib.Path(file_path).name

        r_uploaded_content = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/content/groups/0?',
            headers=self.headers,
            data=self.data,
        )
        res = {}
        for entity in r_uploaded_content.json()['content']:
            res[entity['name']] = entity['id']

        self.logger.info(f"Received content: {res}")

        return res.get(file_name)

    def add_content(self, file_path: str) -> None:
        """
        Add media file to storage if it doesn't already exist there.
        :param file_path: path to media file on server
        :return: None
        """
        # get filename form file path
        file_name = pathlib.Path(file_path).name
        self.logger.info(f"Prepare to add {file_name}")

        # get names of existed media files
        r_existed_content = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/content/groups/0?',
            headers=self.headers,
            data=self.data
        )
        existed_content = {content['name'] for content in r_existed_content.json()['content']}

        if file_name not in existed_content:

            # get size of file in bytes
            size = os.path.getsize(file_path)

            # request data for upload file
            data_ = {
                'name': file_name,
                'group_id': 0,
                'size': size,
                'decode': True,
            }
            with open(file_path, "rb") as f:

                if size < 512_000:
                    self.logger.info("Uploading entire object...")

                    # file is represented in bytes
                    files = {
                        'chunk': f,
                    }
                    self.session.post(
                        f'https://api.ar.digital/v5/platforms/{self.platform_id}/content/file/upload',
                        headers=self.headers,
                        files=files,
                        data=data_
                    )

                else:

                    # needed for add extra headers with content-length
                    headers = self.headers

                    file_id = None

                    for chunk in utils.read_in_chunks(f, 512_000):
                        self.logger.info("Uploading object by chunks")

                        files = {
                            'chunk': chunk,
                        }
                        headers['content-length'] = f'{len(chunk)}'

                        r_chunk_res = self.session.post(
                            f'https://api.ar.digital/v5/platforms/{self.platform_id}/content/file/upload',
                            headers=headers,
                            files=files,
                            data=data_
                        )

                        if file_id is None:
                            file_id = r_chunk_res.json()['file_id']
                            data_['file_id'] = file_id,

                self.logger.info(f"{file_name} has been uploaded")
        else:
            self.logger.info(f"{file_name} already added")

    def clear_archive(self) -> None:
        """
        Clear archive.
        :return: None
        """
        self.logger.info("Clearing archive...")
        r_archived_campaigns = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/archive',
            headers=self.headers,
            data=self.data,
        )
        for campaign in r_archived_campaigns.json()['campaigns']:
            self.session.delete(
                f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/{campaign["id"]}',
                headers=self.headers,
                data=self.data,
            )
        self.logger.info("Archive has been cleared")

    def delete_campaigns(self, campaign_ids: list[int] = None) -> None:
        """
        Archive and delete campaigns.
        :param campaign_ids: list of advertising campaigns
        :return: None
        """
        self.logger.info("Deleting playing campaigns...")

        campaigns_for_delete = {}

        playing_campaigns = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/groups/0',
            headers=self.headers,
            data=json.dumps(self.data)
        ).json()['campaigns']

        for campaign in playing_campaigns:
            campaigns_for_delete[campaign['id']] = campaign['status']

        data_ = self.data
        data_['is_archived'] = True  # noqa
        for campaign_id in campaign_ids:
            if campaigns_for_delete[campaign_id] == 'playing':
                self.session.put(
                    f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/{campaign_id}',
                    headers=self.headers,
                    data=json.dumps(data_)
                )
                self.session.delete(
                    f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/{campaign_id}',
                    headers=self.headers,
                    data=self.data
                )
        self.logger.info("All playing campaigns has been deleted")

    def get_campaigns(self) -> list[int]:
        """
        Archive and delete campaigns.
        :return: list[int]
        """
        self.logger.info(f"Receiving campaigns from storage...")
        r_campaigns = self.session.get(
            f'https://api.ar.digital/v5/platforms/{self.platform_id}/campaign/groups/0',
            headers=self.headers,
            data=self.data
        )
        res = [campaign['id'] for campaign in r_campaigns.json()['campaigns']]
        self.logger.info(f"Received campaigns {res}")
        return res

    def add_and_start_campaign(self, created_campaign: dict) -> None:
        """
        Create campaign, put generated data in it by request and start campaign.
        :param created_campaign: dict of advertising campaign parameters.
        :return: None.
        """
        self.logger.info(f"Creating campaign...")

        campaign = self.session.post(
            f'https://api.ar.digital/v6/platforms/{self.platform_id}/campaign',
            headers=self.headers,
            data=json.dumps(created_campaign)
        )

        campaign_id = json.loads(campaign.content)['id']

        self.logger.info(f"Campaign {campaign_id} has been created")
        self.session.put(

            f'https://api.ar.digital/v6/platforms/{self.platform_id}/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(created_campaign)
        )
        self.logger.info(f"Campaign {campaign_id} has been updated")

        self.start_campaign(campaign_id)
