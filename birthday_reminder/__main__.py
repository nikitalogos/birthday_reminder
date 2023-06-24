import argparse

import yaml

from .configs.main_config import MainConfig
from .drivers.file_reader import FileReader
from .utils.colorize import Colorize

if __name__ == "__main__":
    config = MainConfig()

    parser = argparse.ArgumentParser(prog="birthday-reminder", description="Birthday Reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", description="Just read file and check for errors")
    show_parser = subparsers.add_parser("show", description="Show birthdays from file")
    show_parser.add_argument('sort_type', choices=[t.value for t in FileReader.SortTypes])

    for subparser in [validate_parser, show_parser]:
        subparser.add_argument("file_path", type=str, help="Path to the file with birthdays")
        for key, value in config.get_public_vars().items():
            if key == "verbose":
                subparser.add_argument("-v", "--verbose", action="count", default=0)
            else:
                subparser.add_argument(
                    f"--{key.replace('_', '-')}",
                    type=type(value),
                )
    args_dict = vars(parser.parse_args())
    command = args_dict.pop("command")
    sort_type = args_dict.pop("sort_type", None)
    sort_type = FileReader.SortTypes(sort_type) if sort_type else None
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
    except Exception as e:
        print(Colorize.fail(e))
        exit(2)

    match command:
        case "validate":
            print(Colorize.success(f"File {file_path} is valid!"))
            exit(0)
        case "show":
            message = {
                FileReader.SortTypes.year: "year of birth",
                FileReader.SortTypes.date: "month and day of birth",
                FileReader.SortTypes.next: "days to the next birthday",
            }
            message = Colorize.info(f"\nShowing birthdays sorted by {message[sort_type]}:\n")
            print(message)

            dates = reader.get_dates(sort_type)
            chars_for_digit = len(str(len(dates)))
            for idx, date in enumerate(dates):
                print(f'{(idx + 1):{chars_for_digit}}. {date}')
            print()
