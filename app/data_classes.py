from dataclasses import dataclass


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
    start_date: int
    end_date: int


@dataclass
class User:
    login: str
    password: str
