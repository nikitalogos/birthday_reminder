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
            "date_format_no_year": {"type": "string", "required": True, "regex": r"\S+"},
            "calendar_name": {"type": "string", "required": True},
            "calendar_color_id": {"type": "integer", "required": True, "min": 1, "max": 24},
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
        self.date_format_no_year = "%m-%d"

        self.calendar_name = "Birthday Reminder"
        self.calendar_color_id = 17  # lavender

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
