import enum
from dataclasses import dataclass
from datetime import datetime

from dateutil.relativedelta import relativedelta
from strenum import StrEnum

from .utils.colorize import Colorize


@dataclass
class BirthdayEvent:
    date: datetime
    title: str
    google_event: dict | None = None

    @property
    def date_no_year(self):
        return self.date.replace(year=datetime.now().year)

    @property
    def age(self):
        now = datetime.now()
        was_birthday_this_year = (now.month, now.day) >= (self.date.month, self.date.day)
        return now.year - self.date.year - (not was_birthday_this_year)

    @property
    def next_birthday(self):
        next_birthday = self.date + relativedelta(years=self.age + 1)
        return next_birthday

    @property
    def days_until_next_birthday(self):
        return (self.next_birthday - datetime.now()).days

    def __str__(self):
        return (
            f"{self.date.strftime('%Y-%m-%d')} - {self.title} - {Colorize.info(self.age)} years old "
            f"(Will be {Colorize.info(self.age + 1)} in {Colorize.info(self.days_until_next_birthday)} days)"
        )

    def __eq__(self, other):
        if not isinstance(other, BirthdayEvent):
            return NotImplemented
        return (self.date, self.title) == (other.date, other.title)

    def __hash__(self):
        return hash((self.date, self.title))

    @enum.unique
    class SortTypes(StrEnum):
        year = enum.auto()
        date = enum.auto()
        next = enum.auto()

    @classmethod
    def sort_events(cls, events: list, sort_type: SortTypes):
        match sort_type:
            case cls.SortTypes.year:
                return sorted(events, key=lambda d: d.date)
            case cls.SortTypes.date:
                return sorted(events, key=lambda d: d.date_no_year)
            case cls.SortTypes.next:
                return sorted(events, key=lambda d: d.days_until_next_birthday)
            case _:
                raise ValueError(f"Unknown sort type: {sort_type}")
