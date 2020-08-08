import logging
import os
import time


def set_global_config(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                      file_name=None,
                      level=logging.INFO):
    handlers = [logging.StreamHandler()]
    logging.basicConfig(level=level, format=format, handlers=handlers)


def get_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger