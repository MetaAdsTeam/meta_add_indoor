import datetime
import os

import requests
import json

import app.campaign_generator
from app import data_classes as dc, enums
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

    def get_content_id(self, c_name: str) -> int:
        r_uploaded_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0',
            headers=self.headers
        )
        res = {}
        for entity in r_uploaded_content.json()['content']:
            res[entity['name']] = entity['id']

        return res.get(c_name)

    def add_content(self, file_name: str):
        r_existed_content = self.session.get(
            'https://api.ar.digital/v5/platforms/2058/content/groups/0?',
            headers=self.headers
        )
        existed_content = {content['name']: content['id'] for content in r_existed_content.json()['content']}

        if not existed_content.get(file_name):
            size = os.path.getsize(f'{context.content_path}/{file_name}')
            with open(f'{context.content_path}/{file_name}', 'rb') as f:
                files = {'chunk': f}
                data_ = {
                    'name': file_name,
                    'group_id': 0,
                    'size': size}
                self.session.post(
                    'https://api.ar.digital/v5/platforms/2058/content/file/upload',
                    headers=self.headers,
                    files=files, data=data_
                )

    def delete_campaign(self, campaign_id: int):
        data_ = {
            'is_archived': True
        }
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
        campaign_id = json.loads(campaign.content)['id']
        add_camp = self.session.put(f'https://api.ar.digital/v6/platforms/2058/campaign/{campaign_id}',
                                    headers=self.headers,
                                    data=json.dumps(created_campaign))

        self.start_campaign(campaign_id)

    def start(self):
        self.authorization()
        campaigns = self.get_campaigns()
        for cpm in campaigns:
            self.delete_campaign(cpm)
        # campaigns = get_campaigns(session)
        # for cmp in campaigns:
        #     # if cmp.id != 29971:
        #     delete_campaign(session, cmp.id)
        # r_me = session.get('https://api.ar.digital/v5/users/me', headers=headers)
        # existed_content = get_uploaded_content(session)
        #
        # test_func = utils.create_campaign('Тестовая кампания')

        # update_content(session, existed_content)
        # reload_player(session, 30637)
        # pause_campaign(session, 29923)
        # start_campaign(session, 29923)
        # devices = get_devices(session)
        # print(devices)

        data_ = dc.AppTask(
            name='Test campaign',
            content=[
                dc.Content(
                    389317,
                    enums.FourSections.First.value,
                    5,
                ),
                dc.Content(
                    389318,
                    enums.FourSections.Second.value,
                    5,
                ),
                dc.Content(
                    389319,
                    enums.FourSections.Third.value,
                    5,
                ),
                dc.Content(
                    389320,
                    enums.FourSections.Fourth.value,
                    5,
                )
            ],
            device_id=30637,
            project_id=14765,
            start_date=datetime.datetime(2022, 1, 1),
            end_date=datetime.datetime(2022, 5, 5),
        )

        test = app.campaign_generator.create_campaign(data_)

        self.add_and_start_campaign(test)


if __name__ == '__main__':
    handler = AddRealityHandler('nik@brandvision.io', 'qazwsx12')
    handler.start()
