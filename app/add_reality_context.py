import contextlib
import os
from os import path
from typing import Any, Optional

import yaml
import app.data_classes as dc
from app.db_controller import DBController, WithSessionContextManager


class AddRealityContext:

    def __init__(self):
        self.__db_controller: Optional['DBController'] = None
        self.project_path: str = path.dirname(path.dirname(path.realpath(__file__)))
        self.logs_path: str = path.join(self.project_path, 'logs')
        default_config_path: str = path.join(self.project_path, './default.yaml')
        config_path: str = path.join(self.project_path, './config.yaml')
        with open(default_config_path, 'r') as f:
            self.config: dict[str, Any] = yaml.safe_load(f)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                self.config.update(yaml.safe_load(f) or {})
        else:
            with open(config_path, 'w+') as f:
                yaml.dump(self.config, f, default_flow_style=False)

        self.content_path = path.join(self.project_path, './content')
        for folder in (self.logs_path,):
            if not path.exists(folder):
                with contextlib.suppress(Exception):
                    os.mkdir(folder)
        db: dict[str, Any] = self.config['db']
        self.db_config = dc.DBConfig(**db)
        self.secret_key = self.config['secret_key']

    def load_db_controller(self) -> 'DBController':
        if self.__db_controller is None:
            self.__db_controller = DBController(self)
        return self.__db_controller

    @property
    def db_controller(self) -> 'DBController':
        if self.__db_controller is None:
            raise Exception(
                'DB Controller not loaded. Use "load_db_controller()".')
        return self.__db_controller

    @property
    def sc(self) -> 'WithSessionContextManager':
        db_controller = self.load_db_controller()
        return db_controller.with_sc()

    def stop(self) -> None:
        if self.__db_controller is not None:
            self.__db_controller.stop()
