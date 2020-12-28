import os
import pickle
from datetime import datetime

from hendjibi.tools.app_logger import get_logger
from hendjibi.tools.translator import translate as _

logger = get_logger(__name__)


class DataManager(object):
    def __init__(self, file_path):
        self.file_path = file_path
        self.all_entries = list()
        if os.path.isfile(self.file_path):
            try:
                with open(self.file_path, 'rb') as the_file:
                    data = the_file.read()
                self.all_entries = self.load(data)
            except EOFError as e:
                logger.error(_(F'Failed to load entries data, runtime error is: {e}'))
                logger.info(_('Created empty database, previous file renamed for safety'))
                os.rename(self.file_path, F'{self.file_path}_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}')
                with open(self.file_path, 'wb') as f:
                    f.write(self.dump())
            except Exception as e:
                print(e)
        else:
            # no data
            with open(file_path, 'wb') as f:
                f.write(self.dump())

    def save_dump(self):
        dump_data = self.dump()
        try:
            os.rename(self.file_path, F'{self.file_path}.bak')
        except:
            pass
        with open(self.file_path, 'wb') as f:
            f.write(dump_data)

    def dump(self):
        for e in self.all_entries:
            e.dump()
        return pickle.dumps(self.all_entries)

    @staticmethod
    def load(dump_object):
        return pickle.loads(dump_object)

    def add_entry(self, new_entry):
        self.all_entries.append(new_entry)

    def iterate_entries(self):
        for entry in self.all_entries:
            yield entry
