import enum
from dataclasses import dataclass
from datetime import datetime

from dateutil.relativedelta import relativedelta
from strenum import StrEnum

from .configs.main_config import MainConfig
from .utils.colorize import Colorize


@dataclass
class BirthdayEvent:
    date: datetime
    title: str
    config: MainConfig | None = None
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

    _ZODIAC_SIGNS = [
        (("Capricorn", "♑"), (1, 19)),
        (("Aquarius", "♒"), (2, 18)),
        (("Pisces", "♓"), (3, 20)),
        (("Aries", "♈"), (4, 19)),
        (("Taurus", "♉"), (5, 20)),
        (("Gemini", "♊"), (6, 20)),
        (("Cancer", "♋"), (7, 22)),
        (("Leo", "♌"), (8, 22)),
        (("Virgo", "♍"), (9, 22)),
        (("Libra", "♎"), (10, 22)),
        (("Scorpio", "♏"), (11, 21)),
        (("Sagittarius", "♐"), (12, 21)),
        (("Capricorn", "♑"), (12, 31)),  # to handle the case of dates after Dec 21
    ]

    @property
    def zodiac(self):
        for sign in self._ZODIAC_SIGNS:
            if (self.date.month, self.date.day) <= sign[1]:
                return sign[0]
        raise Exception("Date is invalid. That's weird. Shouldn't get here")

    @property
    def display_title(self):
        zodiac_str = ""
        if self.config and self.config.use_zodiac_signs:
            zodiac_str += f" {self.zodiac[1]}"
        if self.config and self.config.use_zodiac_names:
            zodiac_str += f" ({self.zodiac[0]})"
        return f"{self.title}{zodiac_str}"

    def __str__(self):
        return (
            f"{self.date.strftime('%Y-%m-%d')} - {self.display_title} - {Colorize.info(self.age)} years old "
            f"(Will be {Colorize.info(self.age + 1)} in {Colorize.info(self.days_until_next_birthday)} days)"
        )

    def __eq__(self, other):
        if not isinstance(other, BirthdayEvent):
            return NotImplemented
        return (self.date, self.title) == (other.date, other.title)

    def __hash__(self):
        return hash((self.date, self.title))

    @classmethod
    def from_google_event(cls, google_event):
        date = datetime.fromisoformat(google_event["start"]["date"])
        title = google_event["summary"]

        # remove zodiac signs and names from title
        for sign in cls._ZODIAC_SIGNS:
            name, symbol = sign[0]
            title = title.replace(symbol, "")
            title = title.replace(f"({name})", "")
        title = title.strip()

        return BirthdayEvent(date=date, title=title, google_event=google_event)

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
