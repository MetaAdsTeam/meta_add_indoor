import os
from os import path
from typing import Any

import yaml
import app.data_classes as dc


class AddRealityContext:

    def __init__(self):
        self.project_path: str = path.dirname(path.dirname(path.realpath(__file__)))
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
        self.user_config = dc.User(
            self.config['user']['login'],
            self.config['user']['password']
        )
        self.content_path = path.join(self.project_path, './content')
