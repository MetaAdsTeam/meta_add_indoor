import logging
import os
from datetime import datetime
from logging import Formatter, Logger, INFO
from typing import TypeVar

import coloredlogs
from concurrent_log_handler import ConcurrentRotatingFileHandler
import app

L = TypeVar('L', bound=Logger)


def get_logger(logger_name: str = 'root') -> Logger:
    logger_name = logger_name.removesuffix('.py').replace('.', '_')

    _logger = logging.getLogger(logger_name)

    log_file_name = f'{logger_name}_{datetime.utcnow().strftime("%Y_%m_%d")}.log'

    log_file = os.path.join(app.context.logs_path, log_file_name)
    handler = ConcurrentRotatingFileHandler(log_file, "a", 1024 ** 2, 5)
    _logger.setLevel(INFO)

    formatter_str = '%(asctime)s %(levelname)7s [%(name)s]: %(message)s'
    level_style = coloredlogs.parse_encoded_styles('debug=cyan;\
                                                    warning=yellow;\
                                                    error=red;\
                                                    critical=background=red;\
                                                    info=green')

    field_styles = coloredlogs.parse_encoded_styles('asctime=green;\
                                                    levelname=cyan;\
                                                    name=yellow')

    formatter = Formatter(formatter_str)
    handler.setFormatter(formatter)

    coloredlogs.install(level=INFO,
                        level_styles=level_style,
                        field_styles=field_styles,
                        fmt=formatter_str,
                        milliseconds=True)

    _logger.addHandler(handler)
    return _logger
