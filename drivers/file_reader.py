import re
from datetime import datetime
from dataclasses import dataclass

@dataclass
class BirthdayEvent:
    date: datetime
    title: str


@dataclass
class ParseError:
    line_idx: int
    line_text: str
    error_text: str


class FileReader:
    @staticmethod
    def _parse_lines(lines):
        dates: list[BirthdayEvent] = []
        errors: list[ParseError] = []

        for idx, line in enumerate(lines):
            def add_error(error_text):
                errors.append(ParseError(idx, line, error_text))

            line_no_comment_strip = line.split('#')[0].strip()
            if re.fullmatch(r'\s*', line_no_comment_strip):
                continue

            parts = line_no_comment_strip.split()
            if len(parts) < 2:
                add_error('Expected title after date')
                continue
            date_str = parts[0]
            title = line_no_comment_strip[len(date_str):].strip()
            if len(title) == 0:
                add_error('Expected title after date')
                continue

            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                try:
                    date = datetime.strptime(date_str, '%m-%d')
                except ValueError:
                    add_error(f'Wrong date format: "{date_str}". Expected one of: YYYY-MM-DD, MM-DD')
                    continue

            dates.append(BirthdayEvent(date, title))

        return dates, errors

    def __init__(self, file_path):
        with open(file_path) as f:
            self.lines = f.readlines()
        self.dates, self.errors = self._parse_lines(self.lines)


if __name__ == "__main__":
    import pprint
    pprint = pprint.PrettyPrinter(indent=4).pprint

    file_reader = FileReader('../examples/data.txt')
    pprint(file_reader.lines)
    pprint(file_reader.dates)
    pprint(file_reader.errors)
