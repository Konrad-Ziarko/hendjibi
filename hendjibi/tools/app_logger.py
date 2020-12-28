import logging
import os

from hendjibi import PROJECT_NAME_SHORT


def init_logger(cwd) -> logging.Logger:
    logger = logging.getLogger(F'{PROJECT_NAME_SHORT}')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(os.path.join(cwd, F'{PROJECT_NAME_SHORT}.log'))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def get_logger(module_name) -> logging.Logger:
    return logging.getLogger(F'{PROJECT_NAME_SHORT}.{module_name}')


def set_logger_level(level) -> None:
    logger = logging.getLogger(F'{PROJECT_NAME_SHORT}')
    logger.setLevel(level*10)
