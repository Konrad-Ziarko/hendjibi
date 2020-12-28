import os

from hendjibi.pyqt.gui import start_gui
from hendjibi.tools.config import ConfigManager
from hendjibi.tools.app_logger import init_logger

if __name__ == '__main__':
    start_cwd = os.getcwd()
    logger = init_logger(start_cwd)
    try:
        config = ConfigManager(start_cwd)
        start_gui(config)
    except Exception as e:
        logger.critical(F'Application failed due to : {e}')
