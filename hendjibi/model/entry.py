import pickle
from datetime import date
from enum import Enum


class EntryStatus(Enum):
    UNKNOWN = 'Unknown'
    ANNOUNCED = 'Announced'
    ONGOING = 'Ongoing'
    FINISHED = 'Finished'
    SUSPENDED = 'Suspended'
    CANCELED = 'Canceled'


class ProgressStatus(Enum):
    PLANNED = 'Planned'
    CONSUMING = 'Consuming'
    COMPLETED = 'Completed'
    DROPPED = 'Dropped'


class EntryType(Enum):
    ANIME = 'Anime'
    MANGA = 'Manga'
    WEB_COMIC = 'WebComic'
    LIGHT_NOVEL = 'LightNovel'
    VISUAL_NOVEL = 'VisualNovel'
    MANHWA = 'Manhwa'
    DOJIN = 'Dojin'
    OTHER = 'Other'
    UNKNOWN = 'Unknown'


class GenericEntry(object):
    def __init__(self,
                 cover_image=b'',
                 title_english='',
                 title_original='',
                 synonyms='',
                 release_date1=date.today(),
                 release_date2=date.today(),
                 entry_status=EntryStatus.UNKNOWN,
                 description='',
                 nsfw=False,
                 entry_type=EntryType.UNKNOWN,
                 progress=0,
                 max_progress=0,
                 progress_status=ProgressStatus.PLANNED
                 ):
        self.cover_image = cover_image  # type: bytes
        self.title_english = title_english  # type: str
        self.title_original = title_original  # type: str
        self.synonyms = synonyms  # type: str
        self.release_date1 = release_date1  # type: date
        self.release_date2 = release_date2  # type: date
        self.entry_status = entry_status  # type: EntryStatus
        self.description = description  # type: str
        self.nsfw = nsfw  # type: bool
        self.entry_type = entry_type  # type: EntryType
        self.progress = progress  # type: int
        self.max_progress = max_progress  # type: int
        self.progress_status = progress_status  # type: ProgressStatus

    def set_status(self, new_status):
        self.entry_status = new_status
        if new_status in [EntryStatus.ONGOING, EntryStatus.UNKNOWN, EntryStatus.ANNOUNCED]:
            self.max_progress = 0

    def add_one_progress(self):
        self.progress += 1
        if self.entry_status is EntryStatus.COMPLETED:
            if self.progress == self.max_progress:
                self.progress_status = ProgressStatus.COMPLETED

    def set_progress(self, progress_value):
        if self.entry_status is EntryStatus.COMPLETED:
            self.progress = min(progress_value, self.max_progress)
            if self.progress == self.max_progress:
                self.progress_status = ProgressStatus.COMPLETED
        else:
            self.progress = progress_value

    def mark_done(self):
        if self.entry_status not in [EntryStatus.UNKNOWN, EntryStatus.ONGOING]:
            pass
        else:
            pass

    def get_type(self):
        return self.entry_type.value

    def __str__(self):
        if self.title_english != '':
            return self.title_english
        elif self.title_original != '':
            return self.title_original
        elif self.synonyms != '':
            return self.synonyms
        else:
            return '[Missing data]'

    def __repr__(self):
        return self.__str__()

    def dump(self):
        return pickle.dumps(self)

    def __getstate__(self):
        state = self.__dict__.copy()
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    @staticmethod
    def load_dumped(dump_object):
        return pickle.loads(dump_object)
