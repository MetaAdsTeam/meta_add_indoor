import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Device:
    id: int
    name: str


@dataclass
class Campaign:
    name: str
    id: int


@dataclass
class AdTaskConfig:
    name: str
    device_id: int
    user_data: 'User'
    from_time: datetime.datetime
    to_time: datetime.datetime


@dataclass
class User:
    login: str
    password: str
    platform_id: int


@dataclass
class TaskWrapper:
    task: Optional['AdTaskConfig']
    switch_to: bool


@dataclass
class DBConfig:
    server: str
    port: int
    name: str
    login: str
    password: str
    pool_size: int = field(default=25)
    max_overflow: int = field(default=100)

    @property
    def db_con_string(self) -> str:
        return f'postgresql://{self.login}:{self.password}' \
               f'@{self.server}:{self.port}/{self.name}'

    @property
    def async_db_con_string(self) -> str:
        return f'postgresql+asyncpg://{self.login}:{self.password}' \
               f'@{self.server}:{self.port}/{self.name}'

