import os.path
import sys

import yaml
from cerberus import Validator

from birthday_reminder.configs.base_config import BaseConfig

if getattr(sys, 'frozen', False):
    # Running as a frozen executable
    _THIS_FILE_DIR = os.path.dirname(sys.executable)
    _PROJECT_DIR = _THIS_FILE_DIR
else:
    # Running in a development environment
    _THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_DIR = os.path.dirname(os.path.dirname(_THIS_FILE_DIR))

DEFAULT_CONFIG_FILE = os.path.join(_THIS_FILE_DIR, "default_config.yaml")  # only accessible in dev environment
MAIN_CONFIG_FILE = os.path.join(_PROJECT_DIR, "main_config.yaml")


class MainConfig(BaseConfig):
    @staticmethod
    def _validate(data: dict):
        request_schema = {
            "input_file": {"type": "string", "required": True},
            # "date_format_year": {"type": "string", "required": True, "regex": r"\S+"},
            # "date_format_no_year": {"type": "string", "required": True, "regex": r"\S+"},
            "use_zodiac_signs": {"type": "boolean", "required": True},
            "use_zodiac_names": {"type": "boolean", "required": True},
            "title_prefix": {"type": "string", "required": True},
            "title_postfix": {"type": "string", "required": True},
            "calendar_name": {"type": "string", "required": True},
            "google_oauth_port": {"type": "integer", "required": True, "min": 1025, "max": 65535},
            "use_time": {"type": "boolean", "required": True},
            "time_zone": {"type": "string", "required": True},
            "event_time": {"type": "string", "required": True, "regex": r"\d\d:\d\d"},
            "event_duration": {"type": "string", "required": True, "regex": r"\d\d:\d\d"},
            "remind_29_feb_on_1_mar": {"type": "boolean", "required": True},
            "popup_reminders_minutes": {"type": "list", "required": True, "schema": {"type": "integer"}},
            "email_reminders_minutes": {"type": "list", "required": True, "schema": {"type": "integer"}},
            "verbose": {"type": "integer", "required": True, "min": 0},
        }
        validator = Validator(request_schema)

        if not validator.validate(data):
            errors_dict = validator.errors
            errors_str = yaml.dump(errors_dict)
            raise Exception(f"Validation failed:\n---\n{errors_str}---")

        max_reminders_per_event = 5
        if len(data["popup_reminders_minutes"] + data["email_reminders_minutes"]) > max_reminders_per_event:
            l1 = len(data["popup_reminders_minutes"])
            l2 = len(data["email_reminders_minutes"])
            raise Exception(
                f"Too many reminders. Max reminders number is {max_reminders_per_event}.\n"
                f"Got {l1} in 'popup_reminders_minutes' and {l2} in 'email_reminders_minutes', total: {l1 + l2}"
            )

    def __init__(self):
        super().__init__()

        self.input_file = os.path.join(_PROJECT_DIR, "Birthdays.txt")

        # self.date_format_year = "%Y-%m-%d"  # won't support fancy formats for now. Maybe later.
        # self.date_format_no_year = "%m-%d"
        self.use_zodiac_signs = False
        self.use_zodiac_names = False
        self.title_prefix = "🎁 "
        self.title_postfix = ""

        self.calendar_name = "Birthday Reminder"

        self.google_oauth_port = 58585

        self.use_time = False
        self.time_zone = "UTC"
        self.event_time = "12:00"
        self.event_duration = "01:00"

        self.remind_29_feb_on_1_mar = False

        self.popup_reminders_minutes = [10, 60 * 24 * 7]
        self.email_reminders_minutes = [10, 60 * 24, 60 * 24 * 7]
        self.verbose = 0

        self._validate(self.get_public_vars())

    def set_public_vars(self, data_dict):
        data = self.get_public_vars()
        data.update(data_dict)
        self._validate(data)
        super().set_public_vars(data)


if __name__ == "__main__":
    config = MainConfig()
    print(repr(config))
