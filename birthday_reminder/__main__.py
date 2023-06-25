import argparse

import yaml

from .birthday_event import BirthdayEvent
from .configs.main_config import MainConfig
from .drivers.file_reader import FileReader
from .drivers.google_calendar_api import GoogleCalendarApi
from .utils.colorize import Colorize


def print_events(events: list[BirthdayEvent]):
    chars_for_digit = len(str(len(events)))
    for idx, event in enumerate(events):
        print(f"{(idx + 1):{chars_for_digit}}. {event}")
    print()


def show(events: list[BirthdayEvent], sort_type: BirthdayEvent.SortTypes):
    message = {
        BirthdayEvent.SortTypes.year: "year of birth",
        BirthdayEvent.SortTypes.date: "month and day of birth",
        BirthdayEvent.SortTypes.next: "days to the next birthday",
    }
    message = Colorize.info(f"\nShowing birthdays sorted by {message[sort_type]}:\n")
    print(message)

    events_sorted = BirthdayEvent.sort_events(events, sort_type)
    print_events(events_sorted)


def diff(config, file_events, google_events):
    file_events_set = set(file_events)
    # impossible, already checked in FileReader
    assert len(file_events_set) == len(file_events), "File contains duplicates"

    google_events_set = set(google_events)
    if len(google_events_set) != len(google_events):
        print(
            Colorize.warning(
                "Google Calendar contains duplicates. Did you edit the calendar manually? "
                "This is not an error, duplicates will be ignored. They will go away after you run 'upload' command."
            )
        )

    common_events = file_events_set & google_events_set
    file_only_events = file_events_set - google_events_set
    google_only_events = google_events_set - file_events_set

    print(
        Colorize.info(
            f"File has {len(file_events_set)} events, Google Calendar has {len(google_events_set)} events.\n"
            f"{len(common_events)} events are common,\n"
            f"{len(file_only_events)} events are only in file,\n"
            f"{len(google_only_events)} events are only in Google Calendar.\n"
        )
    )
    if len(file_only_events) > 0:
        print(Colorize.warning("Events only in file:"))
        print_events(list(file_only_events))
    if len(google_only_events) > 0:
        print(Colorize.warning("Events only in Google Calendar:"))
        print_events(list(google_only_events))
    if config.verbose and len(common_events) > 0:
        print(Colorize.info("Common events:"))
        print_events(list(common_events))


if __name__ == "__main__":
    config = MainConfig()

    parser = argparse.ArgumentParser(prog="birthday-reminder", description="Birthday Reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", description="Just read file and check for errors")
    show_parser = subparsers.add_parser("show", description="Show birthdays from file")
    gshow_parser = subparsers.add_parser("gshow", description="Show birthdays from Google Calendar")
    diff_parser = subparsers.add_parser("diff", description="Show differences between file and Google Calendar")

    for subparser in [show_parser, gshow_parser]:
        subparser.add_argument("sort_type", choices=[t.value for t in list(BirthdayEvent.SortTypes)])

    for subparser in [validate_parser, show_parser, diff_parser]:
        subparser.add_argument("file_path", type=str, help="Path to the file with birthdays")

    for subparser in [validate_parser, show_parser, gshow_parser]:
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
    sort_type = BirthdayEvent.SortTypes(sort_type) if sort_type else None
    file_path = args_dict.pop("file_path", None)

    args_dict_no_nones = {k: v for k, v in args_dict.items() if v is not None}
    try:
        config.set_public_vars(args_dict_no_nones)
    except Exception as e:
        print(Colorize.fail(e))
        exit(1)
    if config.verbose:
        print(f"Configuration:\n---\n{yaml.dump(config.get_public_vars())}---")

    if file_path is not None:
        try:
            reader = FileReader(config, file_path)
            file_events = reader.events
        except Exception as e:
            print(Colorize.fail(e))
            exit(2)

    if command in ["gshow", "diff"]:
        try:
            gc_api = GoogleCalendarApi(config)
            google_events = gc_api.get_events()
        except Exception as e:
            print(Colorize.fail(e))
            exit(3)

    match command:
        case "validate":
            print(Colorize.success(f"File {file_path} is valid!"))
            exit(0)
        case "show":
            show(file_events, sort_type)
        case "gshow":
            show(google_events, sort_type)
        case "diff":
            diff(config, file_events=file_events, google_events=google_events)
