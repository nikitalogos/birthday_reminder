#!/bin/sh
"exec" "`dirname $0`/../venv/bin/python" "$0" "$@"

import argparse
import yaml

from configs.main_config import MainConfig
from drivers.file_reader import FileReader
from utils.colorize import Colorize


if __name__ == "__main__":
    config = MainConfig()

    parser = argparse.ArgumentParser(description="Birthday Reminder")
    parser.add_argument("file_path", type=str, help="Path to the file with birthdays")
    for key, value in config.get_public_vars().items():
        if key == "verbose":
            parser.add_argument("-v", "--verbose", action="count", default=0)
        else:
            parser.add_argument(
                f"--{key.replace('_', '-')}",
                type=type(value),
            )
    args_dict = vars(parser.parse_args())
    file_path = args_dict.pop("file_path")

    args_dict_no_nones = {k: v for k, v in args_dict.items() if v is not None}
    try:
        config.set_public_vars(args_dict_no_nones)
    except Exception as e:
        print(Colorize.fail(e))
        exit(1)
    if config.verbose:
        print(f"Configuration:\n---\n{yaml.dump(config.get_public_vars())}---")

    try:
        reader = FileReader(config, file_path)
    except ValueError as e:
        print(Colorize.fail(e))
        exit(2)
