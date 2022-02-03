import os

import requests
import json

from app import data_classes as dc
from app import context


class AddRealityHandler:
    def __init__(self):
        self.session = requests.session()
        self.data = {'login': context.user_config.login, 'password': context.user_config.password}

    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) "
                             "Chrome/83.0.4103.97 Safari/537.36"}

    def reload_player(self, device_id: int) -> None:
        options_resp = self.session.options(f'https://api.ar.digital/v5/platforms/2058/devices/{device_id}',
                                            headers=self.headers)
        if options_resp.status_code == 200:
            with open('./payload.json') as json_file:
                reload_data = json.load(json_file)
            self.session.put(f'https://api.ar.digital/v5/platforms/2058/devices/{device_id}', headers=self.headers,
                             data=json.dumps(reload_data))
        else:
            print("can't reload")

    def get_devices(self) -> list['dc.Device']:
        devices_json = self.session.get('https://api.ar.digital/v5/platforms/2058/devices', headers=self.headers).json()
        res = [dc.Device(device['id'], device['name'], device['status']) for device in devices_json['devices']]
        return res

    def authorization(self):
        r_start_auth = self.session.post('https://api.ar.digital/v5/auth/login/multi_step/start',
                                         headers=self.headers).json()
        self.data['session_id'] = r_start_auth['session_id']

        r_post_login = self.session.post('https://api.ar.digital/v5/auth/login/multi_step/check_login',
                                         headers=self.headers,
                                         data=json.dumps(self.data))

        r_post_pass = self.session.post('https://api.ar.digital/v5/auth/login/multi_step/commit_pwd',
                                        headers=self.headers,
                                        data=json.dumps(self.data))

        r_end_auth = self.session.post('https://api.ar.digital/v5/auth/login/multi_step/finish', headers=self.headers,
                                       data=json.dumps(self.data))
        for resp in [r_post_login, r_post_pass, r_end_auth]:
            if resp.status_code != 200:
                return False
        return True

    def pause_campaign(self, campaign_id):
        pause_ping = {
            'status': 'paused'
        }
        self.session.put(f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}', headers=self.headers,
                         data=json.dumps(pause_ping))

    def start_campaign(self, campaign_id):
        play_ping = {
            'status': 'playing'
        }
        self.session.put(f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}', headers=self.headers,
                         data=json.dumps(play_ping))

    def get_content_id(self, file_path: str) -> int:
        file_name = file_path.split('/')[-1]
        print('get content file_name', file_name)
        r_uploaded_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0?',
            headers=self.headers
        )
        print('get content uploaded content req', r_uploaded_content)
        print('\n')
        print('get content uploaded content', r_uploaded_content.json())
        res = {}
        for entity in r_uploaded_content.json()['content']:
            res[entity['name']] = entity['id']
        print(res)
        return res.get(file_name)

    @staticmethod
    def read_in_chunks(file_object, chunk_size):
        while True:
            data = file_object.read(chunk_size)
            if not data:
                break
            yield data

    def add_content(self, file_path: str):
        file_name = file_path.split('/')[-1]
        print('add_content file_name', file_name)
        r_existed_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0?',
            headers=self.headers
        )
        print('add_content existed_content', r_existed_content.json())
        existed_content = {content['name']: content['id'] for content in r_existed_content.json()['content']}

        if not existed_content.get(file_name):
            size = os.path.getsize(file_path)
            print('add_content size', size)
            file_id = None
            chunk_id = None
            headers = self.headers

            data_ = {
                'name': file_name,
                'group_id': 0,
                'size': size,
                'decode': True,
            }
            file_object = open(file_path, "rb")
            if size < 512_000:
                print('\n')
                print('file less than 512_000\n')
                files = {
                    'chunk': file_object,
                }
                chunk_res = self.session.post(
                    'https://api.ar.digital/v5/platforms/2058/content/file/upload',
                    headers=headers,
                    files=files, data=data_
                )
                print('add_content < 512 ', chunk_res)
                print('add_content < 512 ', chunk_res.json())
                file_id = chunk_res.json()['content']['id']
                print('add_content file_id', file_id)
            else:
                for chunk in self.read_in_chunks(file_object, 512_000):
                    print('file more than 512_000\n')
                    files = {
                        'chunk': chunk,
                    }
                    headers['content-length'] = f'{len(chunk)}'

                    chunk_res = self.session.post(
                        'https://api.ar.digital/v5/platforms/2058/content/file/upload',
                        headers=headers,
                        files=files, data=data_
                    )
                    print('add_content ', chunk_res)
                    print('add_content ', chunk_res.json())
                    if chunk_id is None:
                        chunk_id = chunk_res.json()['file_id']
                        data_['file_id'] = chunk_id,
                    print('add_content file_id', chunk_id)
            print()
            print('content has been added')

    def clear_archive(self):
        r_archived_campaigns = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/campaign/archive',
            headers=self.headers)
        for campaign in r_archived_campaigns.json()['campaigns']:
            self.session.delete(f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign["id"]}',
                                headers=self.headers)

    def delete_campaigns(self, campaign_ids: list[int] = None):
        if campaign_ids is None:
            campaign_ids = self.get_campaigns()
        data_ = {
            'is_archived': True
        }
        for campaign_id in campaign_ids:
            self.session.put(f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}', headers=self.headers,
                             data=json.dumps(data_))
            self.session.delete(f'https://api.ar.digital/v5/platforms/2058/campaign/{campaign_id}', headers=self.headers)

    def get_campaigns(self):
        campaigns = self.session.get('https://api.ar.digital/v5/platforms/2058/campaign/groups/0',
                                     headers=self.headers).json()
        res = [campaign['id'] for campaign in campaigns['campaigns']]
        return res

    def add_and_start_campaign(self, created_campaign):
        campaign = self.session.post('https://api.ar.digital/v6/platforms/2058/campaign', headers=self.headers,
                                     data=json.dumps(created_campaign))
        print(campaign.content)
        campaign_id = json.loads(campaign.content)['id']
        add_camp = self.session.put(f'https://api.ar.digital/v6/platforms/2058/campaign/{campaign_id}',
                                    headers=self.headers,
                                    data=json.dumps(created_campaign))

        self.start_campaign(campaign_id)
