import pytest

from birthday_reminder.configs.main_config import MainConfig
from birthday_reminder.drivers.file_reader import FileReader


class TestFileReader:
    def test_read_good_file(self, utils):
        FileReader(config=MainConfig(), file_path=utils.test_resource("birthdays_no_errors.txt"))

    def test_read_bad_file(self, utils):
        with pytest.raises(ValueError):
            FileReader(config=MainConfig(), file_path=utils.test_resource("birthdays_errors.txt"))
