from datetime import datetime

import pytest

from birthday_reminder.birthday_event import BirthdayEvent
from birthday_reminder.configs.main_config import MainConfig
from birthday_reminder.drivers.file_reader import FileReader


class TestFileReader:
    @staticmethod
    def _year_to_str(year: int):
        return datetime(year, 1, 1).strftime("%Y")

    DEFAULT_YEAR = 1904
    DEFAULT_YEAR_ALT = 2000

    YEAR_PLUS_100 = datetime.now().year + 100
    YEAR_PLUS_1000 = datetime.now().year + 1000
    YEAR_MINUS_100 = datetime.now().year - 100
    YEAR_MINUS_1000 = datetime.now().year - 1000

    @staticmethod
    def _get_verbose_config():
        config = MainConfig()
        config.verbose = 1000
        return config

    @pytest.mark.parametrize(
        "line",
        [
            # basic lines
            (
                "2001-01-01 Ivan",  # one word title
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                "2001-01-01 Ivan Ivanovich",  # multi word title
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan Ivanovich", has_year=True, config=MainConfig()),
            ),
            # comments
            (
                "# full line comment\n2001-01-01 Ivan Ivanovich",  # full line comment
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan Ivanovich", has_year=True, config=MainConfig()),
            ),
            (
                "\t  \t# full line comment\n2001-01-01 Ivan Ivanovich",  # full line comment + leading whitespace
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan Ivanovich", has_year=True, config=MainConfig()),
            ),
            (
                "2001-01-01 Ivan Ivanovich # inline comment",  # inline comment
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan Ivanovich", has_year=True, config=MainConfig()),
            ),
            # whitespaces
            (
                " \t  2001-01-01 Ivan",  # leading whitespace
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                "2001-01-01 Ivan Ivanovich   \t\t",  # trailing whitespace
                BirthdayEvent(date=datetime(2001, 1, 1), title="Ivan Ivanovich", has_year=True, config=MainConfig()),
            ),
            # no-year dates
            (
                "01-01 Ivan",  # no-year date
                BirthdayEvent(date=datetime(DEFAULT_YEAR, 1, 1), title="Ivan", has_year=False, config=MainConfig()),
            ),
            (
                "01-01 Ivan",  # no-year date
                BirthdayEvent(
                    date=datetime(DEFAULT_YEAR_ALT, 1, 1),  # check that passing year makes no difference
                    title="Ivan",
                    has_year=False,
                    config=MainConfig(),
                ),
            ),
            # far from now years
            (
                f"{_year_to_str(YEAR_MINUS_1000)}-01-01 Ivan",
                BirthdayEvent(date=datetime(YEAR_MINUS_1000, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                f"{_year_to_str(YEAR_MINUS_100)}-01-01 Ivan",
                BirthdayEvent(date=datetime(YEAR_MINUS_100, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                f"{_year_to_str(YEAR_PLUS_100)}-01-01 Ivan",
                BirthdayEvent(date=datetime(YEAR_PLUS_100, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                f"{_year_to_str(YEAR_PLUS_1000)}-01-01 Ivan",
                BirthdayEvent(date=datetime(YEAR_PLUS_1000, 1, 1), title="Ivan", has_year=True, config=MainConfig()),
            ),
            # leap years and february 29
            (
                "2020-02-29 Ivan",  # 29 feb, leap year
                BirthdayEvent(date=datetime(2020, 2, 29), title="Ivan", has_year=True, config=MainConfig()),
            ),
            (
                "02-29 Ivan",  # 29 feb, no-year date
                BirthdayEvent(date=datetime(DEFAULT_YEAR, 2, 29), title="Ivan", has_year=False, config=MainConfig()),
            ),
        ],
    )
    def test_good_lines(self, tmpdir, line):
        string, reference_event = line

        filepath = tmpdir.join("good_file.txt")
        filepath.write(string)

        config = self._get_verbose_config()
        config.input_file = filepath
        reader = FileReader(config=config)

        assert len(reader.events) == 1
        print(f"Parsed:\n{reader.events[0]}")
        print(f"Reference:\n{reference_event}")
        assert reader.events[0] == reference_event

    @pytest.mark.parametrize(
        "line",
        [
            "2001-01-01",  # no title
            "Ivan Ivanovich",  # no date
            "2001-01-01Ivan Ivanovich",  # no space between date and title
            # invalid day
            "1985-05-00 Ivan",
            "1985-05-38 Ivan",
            # invalid month
            "1985-00-01 Ivan",
            "1985-13-01 Ivan",
            # invalid year
            "985-05-01 Ivan",
            "19850-05-01 Ivan",
            "01985-05-01 Ivan",
            # 29 feb, no leap year
            "1900-02-29 Ivan",
            "2023-02-29 Ivan",
        ],
    )
    def test_bad_lines(self, tmpdir, line):
        with pytest.raises(ValueError):
            filepath = tmpdir.join("bad_file.txt")
            filepath.write(line)

            config = self._get_verbose_config()
            config.input_file = filepath
            reader = FileReader(config=config)
            print(reader.events[0])

    def test_read_good_file(self, utils):
        config = self._get_verbose_config()
        config.input_file = utils.test_resource("birthdays_no_errors.txt")
        FileReader(config=config)

    def test_read_bad_file(self, utils):
        with pytest.raises(ValueError):
            config = self._get_verbose_config()
            config.input_file = utils.test_resource("birthdays_errors.txt")
            FileReader(config=config)
