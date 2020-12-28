import configparser
import os
from enum import Enum

from hendjibi import PROJECT_NAME_SHORT
from hendjibi.tools.app_logger import get_logger
from hendjibi.tools.translator import translate as _
from hendjibi.model.entry import ProgressStatus, EntryType

logger = get_logger(__name__)

SLIDER_MIN = 50
SLIDER_MAX = 250


class ConfigSection(Enum):
    MAIN = 'Main'
    VIEW = 'View'
    PROGRESS_STATUS = ProgressStatus.__name__
    ENTRY_TYPE = EntryType.__name__


class ConfigManager(object):
    PROPERTIES = [
        ('data_dump_path', ConfigSection.MAIN, str, os.path.join('hdb', 'entries.data'), None, None),
        ('height', ConfigSection.MAIN, int, 600, 200, None),
        ('width', ConfigSection.MAIN, int, 800, 300, None),
        ('log_level', ConfigSection.MAIN, int, 2, 0, 5),
        ('redraw_on_release', ConfigSection.VIEW, bool, False, None, None),
        ('stay_on_top', ConfigSection.VIEW, bool, False, None, None),
        ('dark_mode', ConfigSection.VIEW, bool, True, None, None),
        ('slider', ConfigSection.VIEW, int, 150, SLIDER_MIN, SLIDER_MAX),
    ]

    def __init__(self, cwd):
        path = os.path.join(cwd, PROJECT_NAME_SHORT)
        if not os.path.isdir(path):
            os.mkdir(path)
        self.config_path = os.path.join(path, '{}.ini'.format(PROJECT_NAME_SHORT))
        self.config = configparser.ConfigParser()

        try:
            self.config.read(self.config_path)
            for section in ConfigSection:
                if not self.config.has_section(section.value):
                    self.config.add_section(section.value)
        except Exception as e:
            logger.error(_(F'Could not open config file due to: {e}'))

        for property_to_add in ConfigManager.PROPERTIES:
            ConfigManager.add_property(*property_to_add)
        for progress_status_type in ProgressStatus:
            name = progress_status_type.value.lower()
            ConfigManager.add_property(name, ProgressStatus.__name__, bool, True)
        for entry_type in EntryType:
            name = entry_type.value.lower()
            ConfigManager.add_property(name, EntryType.__name__, bool, True)
        self.read_config()

    @staticmethod
    def add_property(name, tag, prop_type, default_value, min_value=None, max_value=None):
        if not isinstance(tag, str):
            tag = tag.value
        setattr(ConfigManager, '_default_{}'.format(name), default_value)

        def setter_method(this, value):
            if issubclass(prop_type, int):
                if min_value is not None:
                    if value < min_value:
                        value = min_value
                if max_value is not None:
                    if value > max_value:
                        value = max_value
            this.config.set(tag, name, str(value))
            setattr(this, '_{}'.format(name), value)
            this.write_config()
        getter_method = property(lambda x: getattr(x, '_{}'.format(name)), setter_method)
        setattr(ConfigManager, '_{}'.format(name), default_value)
        setattr(ConfigManager, name, getter_method)

    def read_config(self):
        for property_to_read in ConfigManager.PROPERTIES:
            try:
                if issubclass(property_to_read[2], int):
                    v = self.config.getint(property_to_read[1].value, property_to_read[0])
                elif issubclass(property_to_read[2], bool):
                    v = self.config.getboolean(property_to_read[1].value, property_to_read[0])
                elif issubclass(property_to_read[2], str):
                    v = self.config.get(property_to_read[1].value, property_to_read[0])
                else:
                    raise Exception('Property with unhandled type!')
                setattr(self, property_to_read[0], v)
            except (configparser.NoOptionError, ValueError):
                setattr(self, property_to_read[0], property_to_read[3])
        for property_to_read in ProgressStatus:
            prop_name = property_to_read.value.lower()
            try:
                v = self.config.getboolean(ProgressStatus.__name__, prop_name)
                setattr(self, prop_name, v)
            except (configparser.NoOptionError, ValueError):
                setattr(self, prop_name, True)
        for property_to_read in EntryType:
            prop_name = property_to_read.value.lower()
            try:
                v = self.config.getboolean(EntryType.__name__, prop_name)
                setattr(self, prop_name, v)
            except (configparser.NoOptionError, ValueError):
                setattr(self, prop_name, True)

    def write_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
