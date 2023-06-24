import enum
import re
from dataclasses import dataclass
from datetime import datetime

from strenum import StrEnum

from ..birthday_event import BirthdayEvent
from ..utils.colorize import Colorize


@dataclass
class TextLine:
    line_idx: int
    line_text: str

    def __str__(self):
        return Colorize.info(f"{self.line_idx}:") + f" {self.line_text}"


@dataclass
class BirthdayLine(TextLine):
    event: BirthdayEvent

    def __str__(self):
        return Colorize.info(f"{self.line_idx}:") + f" {self.line_text} -> " + Colorize.success(self.event)


@dataclass
class ParseError(TextLine):
    error_text: str

    def __str__(self):
        return Colorize.info(f"{self.line_idx}:") + f" {self.line_text} -> " + Colorize.fail(self.error_text)


class FileReader:
    @staticmethod
    def _parse_lines(lines):
        dates: list[BirthdayLine] = []
        errors: list[ParseError] = []
        text_lines: list[TextLine] = []

        for idx, line in enumerate(lines):

            def add_error(error_text):
                pe = ParseError(idx, line_no_end, error_text)
                errors.append(pe)
                text_lines.append(pe)

            line_no_end = line.rstrip("\n")

            line_no_comment_strip = line.split("#")[0].strip()
            if re.fullmatch(r"\s*", line_no_comment_strip):
                text_lines.append(TextLine(idx, line_no_end))
                continue

            parts = line_no_comment_strip.split()
            if len(parts) < 2:
                add_error("Expected title after date")
                continue
            date_str = parts[0]
            title = line_no_comment_strip[len(date_str) :].strip()
            if len(title) == 0:
                add_error("Expected title after date")
                continue

            try:
                date = datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    date = datetime.strptime(date_str, "%m-%d")
                except ValueError:
                    add_error(f'Wrong date format: "{date_str}". Expected one of: YYYY-MM-DD, MM-DD')
                    continue

            be = BirthdayEvent(date, title)
            bl = BirthdayLine(idx, line_no_end, be)
            dates.append(bl)
            text_lines.append(bl)

        return dates, errors, text_lines

    @staticmethod
    def _visualize_parsed(config, dates, errors, text_lines):
        if len(errors) > 0:
            print(f"Found {len(errors)} errors:\n---")
            for error in errors:
                print(error)
            print("---")

        if config.verbose:
            print(f"Found {len(dates)} dates:\n---")
            for date in dates:
                print(date)
            print("---")

        if config.verbose >= 2:
            print(f"Found {len(text_lines)} lines:\n---")
            for text_line in text_lines:
                print(text_line)
            print("---")

    def __init__(self, config, file_path):
        with open(file_path) as f:
            lines = f.readlines()
        dates, errors, text_lines = self._parse_lines(lines)

        self._visualize_parsed(config, dates, errors, text_lines)
        if len(errors) > 0:
            raise ValueError(f"File has {len(errors)} errors! Please fix them before continuing.")

        self.events = [date.event for date in dates]

    @enum.unique
    class SortTypes(StrEnum):
        year = enum.auto()
        date = enum.auto()
        next = enum.auto()

    def get_dates(self, sort_type: SortTypes):
        match sort_type:
            case self.SortTypes.year:
                return sorted(self.events, key=lambda d: d.date)
            case self.SortTypes.date:
                return sorted(self.events, key=lambda d: d.date_no_year)
            case self.SortTypes.next:
                return sorted(self.events, key=lambda d: d.days_until_next_birthday)
            case _:
                raise ValueError(f"Unknown sort type: {sort_type}")
