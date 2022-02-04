from dataclasses import dataclass
from typing import Optional


@dataclass
class Device:
    id: int
    name: str
    status: str


@dataclass
class Campaign:
    name: str
    id: int


@dataclass
class AdTaskConfig:
    name: str
    from_time: int
    to_time: int


@dataclass
class User:
    login: str
    password: str


@dataclass
class TaskWrapper:
    task: Optional['AdTaskConfig']
    switch_to: bool
