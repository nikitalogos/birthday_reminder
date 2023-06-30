import copy
import dataclasses
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
    has_year: bool
    config: MainConfig | None = None
    google_event: dict | None = None
    is_manually_created_google_event: bool = False

    def __post_init__(self):
        has_config = self.config is not None
        has_google_event = self.google_event is not None
        assert has_config != has_google_event, (
            "Incompatible fields: if event created from google, config makes no sense. "
            "If event created from file, config is required."
        )

    @property
    def date_no_year(self):
        return self.date.replace(year=datetime.now().year)

    @property
    def age(self):
        now = datetime.now()
        was_birthday_this_year = (now.month, now.day) >= (self.date.month, self.date.day)
        return now.year - self.date.year - (not was_birthday_this_year)

    @property
    def is_birthday_today(self):
        now = datetime.now()
        return (now.month, now.day) == (self.date.month, self.date.day)

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
    def _zodiac_str(self):
        zodiac_str = ""
        if self.config and self.config.use_zodiac_signs:
            zodiac_str += f" {self.zodiac[1]}"
        if self.config and self.config.use_zodiac_names:
            zodiac_str += f" ({self.zodiac[0]})"
        return zodiac_str

    @property
    def display_title(self):
        if self.google_event:
            return self.google_event["summary"]

        return f"{self.title}{self._zodiac_str}"

    _UNIQUE_TAG = "#birthday_reminder"
    _DATE_OF_BIRTH_KEY = "Date of birth"
    _NO_YEAR_PLACEHOLDER = "...."
    _GENERATED_BY_STR = "Generated by 'Birthday Reminder'"

    @property
    def description_for_google_calendar(self):
        if self.has_year:
            date_of_birth = self.date.strftime("%Y-%m-%d")
        else:
            date_of_birth = self.date.strftime(f"{self._NO_YEAR_PLACEHOLDER}-%m-%d")

        description = ""
        description += f"{self._DATE_OF_BIRTH_KEY}: {date_of_birth}\n"
        description += f"Zodiac sign: {self.zodiac[1]} ({self.zodiac[0]})\n"
        description += f"{self._GENERATED_BY_STR} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        description += f"{self._UNIQUE_TAG}\n"
        return description

    def __str__(self):
        # if google event and not generated by this program - inform user about data loss risks
        if self.is_manually_created_google_event:
            warn_text = Colorize.warning(
                "Not generated by Birthday Reminder. Did you create it manually? "
                "Move it to other calendar or it may be deleted..."
            )
            return f"{self.date.strftime('%Y-%m-%d')} - {self.display_title} - {warn_text}"

        if self.is_birthday_today:
            title_birthday_str = Colorize.success(f"{self.display_title} celebrates birthday today!")
        else:
            title_birthday_str = self.display_title
        days_str = "days" if self.days_until_next_birthday != 1 else "day"
        if self.has_year:
            return (
                f"{self.date.strftime('%Y-%m-%d')} - {title_birthday_str} - {Colorize.info(self.age)} years old "
                f"(Will be {Colorize.info(self.age + 1)} in {Colorize.info(self.days_until_next_birthday)} {days_str})"
            )
        else:
            return (
                f"{self.date.strftime(f'{self._NO_YEAR_PLACEHOLDER}-%m-%d')} - {title_birthday_str} "
                f"(Next birthday in {Colorize.info(self.days_until_next_birthday)} {days_str})"
            )

    @property
    def _signature(self):
        return self.date, self.title, self.has_year

    @property
    def _google_event_signature(self):
        if self.google_event:
            keys_to_compare = ["summary", "description", "start", "end", "recurrence", "reminders"]
            google_event = {k: v for k, v in self.google_event.items() if k in keys_to_compare}
            google_event = copy.deepcopy(google_event)
        else:
            google_event = self.to_google_event()
        google_event.get("reminders", {}).get("overrides", []).sort(key=lambda x: (x["minutes"], x["method"]))
        google_event["description"] = "\n".join(
            [s for s in google_event.get("description", "").split("\n") if not s.startswith(self._GENERATED_BY_STR)]
        )
        return google_event

    def __eq__(self, other):
        if not isinstance(other, BirthdayEvent):
            return NotImplemented
        return self._signature == other._signature and self._google_event_signature == other._google_event_signature

    def __hash__(self):
        return hash(self._signature)

    @classmethod
    def from_google_event(cls, google_event):
        start = google_event["start"]
        if "dateTime" in start:
            date_str = start["dateTime"][:10]
        else:
            date_str = start["date"]
        date = datetime.strptime(date_str, "%Y-%m-%d")

        title = google_event["summary"]
        # remove zodiac signs and names from title
        for sign in cls._ZODIAC_SIGNS:
            name, symbol = sign[0]
            title = title.replace(symbol, "")
            title = title.replace(f"({name})", "")
        title = title.strip()

        description = google_event.get("description", "")

        lines = description.split("\n")
        date_of_birth_line = next((line for line in lines if line.startswith(cls._DATE_OF_BIRTH_KEY)), "")
        has_year = cls._NO_YEAR_PLACEHOLDER not in date_of_birth_line

        return BirthdayEvent(
            date=date,
            title=title,
            has_year=has_year,
            google_event=google_event,
            is_manually_created_google_event=cls._UNIQUE_TAG not in description,
        )

    def to_google_event(self) -> dict:
        assert self.config, "Config is not set"

        google_event = {
            "summary": self.display_title,
            "description": self.description_for_google_calendar,
            "recurrence": ["RRULE:FREQ=YEARLY"],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "popup", "minutes": minutes} for minutes in self.config.popup_reminders_minutes
                ]
                + [{"method": "email", "minutes": minutes} for minutes in self.config.email_reminders_minutes],
            },
        }

        if self.config.use_time:
            event_time = datetime.strptime(self.config.event_time, "%H:%M")
            event_time_delta = relativedelta(hours=event_time.hour, minutes=event_time.minute)

            event_duration = datetime.strptime(self.config.event_duration, "%H:%M")
            event_duration_delta = relativedelta(hours=event_duration.hour, minutes=event_duration.minute)

            start_datetime = self.date + event_time_delta
            end_datetime = start_datetime + event_duration_delta

            google_event.update(
                {
                    "start": {
                        "dateTime": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "timeZone": self.config.time_zone,
                    },
                    "end": {"dateTime": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": self.config.time_zone},
                }
            )
        else:
            next_day = self.date + relativedelta(days=1)

            google_event.update(
                {
                    "start": {"date": self.date.strftime("%Y-%m-%d")},
                    "end": {"date": next_day.strftime("%Y-%m-%d")},
                }
            )
        return google_event

    @enum.unique
    class SortTypes(StrEnum):
        year = enum.auto()
        date = enum.auto()
        next = enum.auto()

    @classmethod
    def sort_events(cls, events: list, sort_type: SortTypes):
        match sort_type:
            case cls.SortTypes.year:
                events_with_year = sorted([e for e in events if e.has_year], key=lambda d: d.date)
                events_without_year = sorted([e for e in events if not e.has_year], key=lambda d: d.date_no_year)
                return events_with_year + events_without_year
            case cls.SortTypes.date:
                return sorted(events, key=lambda d: d.date_no_year)
            case cls.SortTypes.next:
                return sorted(events, key=lambda d: d.days_until_next_birthday)
            case _:
                raise ValueError(f"Unknown sort type: {sort_type}")


class BirthdayEventSignature(BirthdayEvent):
    def __eq__(self, other):
        if not isinstance(other, BirthdayEvent):
            return NotImplemented
        return self._signature == other._signature

    def __hash__(self):
        return hash(self._signature)

    @classmethod
    def from_event(cls, event):
        return cls(
            date=event.date,
            title=event.title,
            has_year=event.has_year,
            config=event.config,
            google_event=event.google_event,
            is_manually_created_google_event=event.is_manually_created_google_event,
        )


@dataclass
class ComparisonResult:
    file_only_events: set[BirthdayEvent] = dataclasses.field(default_factory=set)
    google_only_events: set[BirthdayEvent] = dataclasses.field(default_factory=set)
    equal_events: set[BirthdayEvent] = dataclasses.field(default_factory=set)
    updated_events: set[BirthdayEvent] = dataclasses.field(default_factory=set)

    @property
    def has_changes(self):
        return any([self.file_only_events, self.google_only_events, self.updated_events])


def compare_events_file_and_google(
    file_events: list[BirthdayEvent], google_events: list[BirthdayEvent]
) -> ComparisonResult:
    file_events_set = set(file_events)
    # impossible, already checked in FileReader
    assert len(file_events_set) == len(file_events), "File contains duplicates"

    google_events_set = set(google_events)
    if len(google_events_set) != len(google_events):
        duplicate_events = [e for e in google_events if google_events.count(e) > 1]
        duplicate_events_str = "\n".join([str(e) for e in duplicate_events])
        assert len(google_events_set) < len(google_events), (
            "Google Calendar contains duplicates. Did you edit the calendar manually?\n"
            "Please delete duplicates manually and try again.\n"
            f"Duplicate events:\n{duplicate_events_str}"
        )

    cmp_result = ComparisonResult()

    cmp_result.equal_events = file_events_set & google_events_set
    file_events_set -= cmp_result.equal_events
    google_events_set -= cmp_result.equal_events

    file_events_signature_set = {BirthdayEventSignature.from_event(e) for e in file_events_set}
    google_events_signature_set = {BirthdayEventSignature.from_event(e) for e in google_events_set}

    cmp_result.updated_events = file_events_signature_set & google_events_signature_set
    cmp_result.file_only_events = file_events_signature_set - google_events_signature_set
    cmp_result.google_only_events = google_events_signature_set - file_events_signature_set
    return cmp_result
