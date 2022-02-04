import contextlib
import os
import pathlib

import requests
import json

from app import data_classes as dc
from app import context
import app.log_lib as log_lib


class AddRealityHandler:
    __logger: 'log_lib' = None

    def __init__(self):
        self.session = requests.session()
        self.data = {'login': context.user_config.login, 'password': context.user_config.password}

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
        self.logger.info('Reloading player')
        options_resp = self.session.options(
            f'https://api.ar.digital/v5/platforms/2058/devices/{device_id}',
            headers=self.headers,
            data=self.data)
        if options_resp.status_code == 200:
            with open('./payload.json') as json_file:
                reload_data = json.load(json_file)
            self.session.put(
                f'https://api.ar.digital/v5/platforms/2058/devices/{device_id}',
                headers=self.headers,
                data=json.dumps(reload_data))
            self.logger.info('Player has been reloaded')
        else:
            self.logger.info("Can't reload player")

    def get_devices(self) -> list['dc.Device']:
        self.logger.info("Receiving devices")
        r_devices_json = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/devices',
            headers=self.headers
        )
        res = [dc.Device(device['id'], device['name'], device['status']) for device in r_devices_json.json()['devices']]
        self.logger.info(f"Received devices: {res}")
        return res

    def authorization(self):
        self.logger.info(f"Authorizing user...")

        data = self.data
        r_start_auth = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/start',
            headers=self.headers
        )
        data['session_id'] = r_start_auth.json()['session_id']

        r_post_login = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/check_login',
            headers=self.headers,
            data=json.dumps(self.data)
        )

        r_post_pass = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/commit_pwd',
            headers=self.headers,
            data=json.dumps(self.data)
        )

        r_end_auth = self.session.post(
            'https://api.ar.digital/v5/auth/login/multi_step/finish',
            headers=self.headers,
            data=json.dumps(self.data)
        )
        for resp in [r_post_login, r_post_pass, r_end_auth]:
            if resp.status_code != 200:
                self.logger.critical(f"The user isn't authorized")
        self.logger.info(f"The user is authorized")

    def pause_campaign(self, campaign_id):
        pause_ping = {
            'status': 'paused'
        }
        self.session.put(
            f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(pause_ping)
        )
        self.logger.info(f"Campaign {campaign_id} has been paused")

    def start_campaign(self, campaign_id):
        play_ping = {
            'status': 'playing'
        }
        self.session.put(
            f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(play_ping)
        )
        self.logger.info(f"Campaign {campaign_id} has been started")

    def get_content_id(self, file_path: str) -> int:
        self.logger.info(f"Receiving content from storage...")
        file_name = pathlib.Path(file_path).name
        r_uploaded_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0?',
            headers=self.headers,
            data=self.data,
        )
        res = {}
        for entity in r_uploaded_content.json()['content']:
            res[entity['name']] = entity['id']

        self.logger.info(f"Received content: {res}")

        return res.get(file_name)

    @staticmethod
    def read_in_chunks(file_object, chunk_size):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    def add_content(self, file_path: str):
        file_name = pathlib.Path(file_path).name
        self.logger.info(f"Prepare to add {file_name}")
        r_existed_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0?',
            headers=self.headers,
            data=self.data
        )
        existed_content = {content['name']: content['id'] for content in r_existed_content.json()['content']}

        if not existed_content.get(file_name):
            size = os.path.getsize(file_path)
            chunk_id = None
            headers = self.headers

            data_ = {
                'name': file_name,
                'group_id': 0,
                'size': size,
                'decode': True,
            }
            with open(file_path, "rb") as f:

                if size < 512_000:
                    self.logger.info("Uploading entire object...")

                    files = {
                        'chunk': f,
                    }
                    self.session.post(
                        'https://api.ar.digital/v5/platforms/2058/content/file/upload',
                        headers=headers,
                        files=files,
                        data=data_
                    )

                else:
                    for chunk in self.read_in_chunks(f, 512_000):
                        self.logger.info("Uploading object by chunks")
                        files = {
                            'chunk': chunk,
                        }
                        headers['content-length'] = f'{len(chunk)}'

                        chunk_res = self.session.post(
                            'https://api.ar.digital/v5/platforms/2058/content/file/upload',
                            headers=headers,
                            files=files,
                            data=data_
                        )
                        if chunk_id is None:
                            chunk_id = chunk_res.json()['file_id']
                            data_['file_id'] = chunk_id,

                self.logger.info(f"{file_name} has been uploaded")
        else:
            self.logger.info(f"{file_name} already added")

    def clear_archive(self):
        self.logger.info("Clearing archive...")
        r_archived_campaigns = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/campaign/archive',
            headers=self.headers,
            data=self.data,
        )
        for campaign in r_archived_campaigns.json()['campaigns']:
            self.session.delete(
                f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign["id"]}',
                headers=self.headers,
                data=self.data,
            )
        self.logger.info("Archive has been cleared")

    def delete_campaigns(self, campaign_ids: list[int] = None):
        self.logger.info("Deleting campaigns...")
        if campaign_ids is None:
            campaign_ids = self.get_campaigns()
        data_ = self.data
        data_['is_archived'] = True
        for campaign_id in campaign_ids:
            self.session.put(
                f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}',
                headers=self.headers,
                data=json.dumps(data_)
            )
            self.session.delete(
                f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}',
                headers=self.headers,
                data=self.data
            )
        self.logger.info("All campaigns has been deleted")

    def get_campaigns(self):
        self.logger.info(f"Receiving campaigns from storage...")
        r_campaigns = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/campaign/groups/0',
            headers=self.headers,
            data=self.data
        )
        res = [campaign['id'] for campaign in r_campaigns.json()['campaigns']]
        self.logger.info(f"Received campaigns {res}")
        return res

    def add_and_start_campaign(self, created_campaign):
        self.logger.info(f"Creating campaign...")

        campaign = self.session.post(
            'https://api.ar.digital/v6/platforms/2058/campaign',
            headers=self.headers,
            data=json.dumps(created_campaign)
        )

        campaign_id = json.loads(campaign.content)['id']

        self.logger.info(f"Campaign {campaign_id} has been created")
        self.session.put(

            f'https://api.ar.digital/v6/platforms/2058/campaign/{campaign_id}',
            headers=self.headers,
            data=json.dumps(created_campaign)
        )
        self.logger.info(f"Campaign {campaign_id} has been updated")

        self.start_campaign(campaign_id)
