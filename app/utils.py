from datetime import datetime, date
from typing import Optional, TypeVar

from app import exceptions

T_Any = TypeVar('T_Any')
T_Any2 = TypeVar('T_Any2')


def datetime_from_string(ts: str, verify: bool = False) -> Optional[datetime]:
    """
    Convert time string to datetime with check on empty source string.
    :param ts: time string
    :param verify: verify if date string is empty
    :return: datetime
    """
    if ts:
        try:
            return datetime.fromisoformat(ts)
        except ValueError:
            raise exceptions.APIError(f'Date argument is not correct.')
    elif verify:
        raise exceptions.APIError(f'Date argument are missed.')
    return None


def date_from_string(ts: str, verify: bool = False) -> Optional[date]:
    """
    Convert time string to date with check on empty source string.
    :param ts: time string
    :param verify: verify if date string is empty
    :return: date
    """
    if ts:
        try:
            return datetime.fromisoformat(ts).date()
        except ValueError:
            raise exceptions.APIError(f'Date argument is not correct.')
    elif verify:
        raise exceptions.APIError(f'Date argument are missed.')
    return None


def date_from_string_safe(ts: str) -> date:
    """
    Date from string without exception throwing.
    :param ts: time string
    :return: date
    """
    try:
        result = date_from_string(ts, True)
    except exceptions.APIError:
        result = date.today()
    return result


def convert_time(start: datetime, end: datetime):
    return int(start.timestamp()), int(end.timestamp())
