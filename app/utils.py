from datetime import datetime, date
from random import random
from typing import Optional, TypeVar

import app
from app import exceptions
from cryptography.fernet import Fernet

T_Any = TypeVar('T_Any')
T_Any2 = TypeVar('T_Any2')
context = app.context


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


def file_id_generator():
    return int(random() * 10 ** 6)


def read_in_chunks(file_object, chunk_size):
    while True:
        data = file_object.read(chunk_size)
        if not data:
            break
        yield data


def encode_password(password: str):
    f = Fernet(context.secret_key)
    encrypted_pass = f.encrypt(password.encode('utf-8'))
    return encrypted_pass


def decode_password(password: bytes):
    f = Fernet(context.secret_key)
    decrypted_pass = f.decrypt(password)
    return decrypted_pass.decode('utf-8')
