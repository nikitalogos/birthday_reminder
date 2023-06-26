import os

import yaml
from cerberus import Validator

from .base_config import BaseConfig

THIS_FILE_DIR = os.path.dirname(os.path.realpath(__file__))
RS_CONFIGS_DIR = f"{THIS_FILE_DIR}/rs_configs"


class MainConfig(BaseConfig):
    @staticmethod
    def _validate(data: dict):
        request_schema = {
            "date_format_year": {"type": "string", "required": True, "regex": r"\S+"},
            # "date_format_no_year": {"type": "string", "required": True, "regex": r"\S+"},
            "use_zodiac_signs": {"type": "boolean", "required": True},
            "use_zodiac_names": {"type": "boolean", "required": True},
            "calendar_name": {"type": "string", "required": True},
            "use_time": {"type": "boolean", "required": True},
            "time_zone": {"type": "string", "required": True},
            "event_time": {"type": "string", "required": True, "regex": r"\d\d:\d\d"},
            "event_duration": {"type": "string", "required": True, "regex": r"\d\d:\d\d"},
            "popup_reminders_minutes": {"type": "list", "required": True, "schema": {"type": "integer"}},
            "email_reminders_minutes": {"type": "list", "required": True, "schema": {"type": "integer"}},
            "verbose": {"type": "integer", "required": True, "min": 0},
        }
        validator = Validator(request_schema)

        if not validator.validate(data):
            errors_dict = validator.errors
            errors_str = yaml.dump(errors_dict)
            raise Exception(f"Validation failed:\n---\n{errors_str}---")

    def __init__(self):
        super().__init__()

        self.date_format_year = "%Y-%m-%d"
        # self.date_format_no_year = "%m-%d"  # todo add support for no-year dates
        self.use_zodiac_signs = False
        self.use_zodiac_names = False
        self.calendar_name = "Birthday Reminder"

        self.use_time = False
        self.time_zone = "UTC"
        self.event_time = "12:00"
        self.event_duration = "01:00"

        self.popup_reminders_minutes = [10, 60 * 24, 60 * 24 * 2, 60 * 24 * 7]
        self.email_reminders_minutes = [10, 60 * 24, 60 * 24 * 2, 60 * 24 * 7]
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
