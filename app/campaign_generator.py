from random import random
from typing import Optional

from app import data_classes as dc, utils


def key_generator():
    return f'{int(random() * 10 ** 16)}-random'


def content_special(
        start_date: int = None,
        end_date: int = None,
        week_days: Optional[list[int]] = None,
        vast_interrupt: Optional[bool] = True,
        duration: int = 60000,
        gender: Optional[int] = 3
):
    content_special_res = {}

    if week_days is None:
        week_days = [1 for _ in range(7)]

    content_special_res['range'] = [start_date, end_date]

    content_special_res['week_days'] = week_days

    content_special_res['vast_interrupt'] = vast_interrupt

    content_special_res['duration'] = duration

    content_special_res['gender'] = gender

    return content_special_res


def create_content(content_id):
    content = [{
        "content_id": content_id,
        "zones": [217226],
        "special": content_special(),
    }]
    return content


def create_campaign(content_id: int, campaign: 'dc.AdTaskConfig'):
    return {
        'gender': 3, 'name': f'{campaign.name}-{utils.file_id_generator()}', 'playlist': [],
        'content': create_content(content_id),
        'project_id': 13441,
        'devices_delta': {
            'selected': [30820]
        },
        'timing': {
            'global': {
                'start': None, 'end': None}
        }
    }
