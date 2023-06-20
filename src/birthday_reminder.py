#!/bin/sh
"exec" "`dirname $0`/venv/bin/python" "$0" "$@"

import argparse

from configs.main_config import MainConfig

if __name__ == "__main__":
    config = MainConfig()

    parser = argparse.ArgumentParser(description="Birthday Reminder")
    for key, value in config.get_public_vars().items():
        parser.add_argument(
            f"--{key}",
            type=type(value),
        )
    args_dict = vars(parser.parse_args())
    args_dict_no_nones = {k: v for k, v in args_dict.items() if v is not None}
    try:
        config.set_public_vars(args_dict_no_nones)
    except Exception as e:
        print(e)
        exit(1)
