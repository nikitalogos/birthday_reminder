import argparse
import copy

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


def diff(config, file_events, google_events) -> int:
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

    return len(file_only_events) + len(google_only_events)


if __name__ == "__main__":
    config = MainConfig()

    parser = argparse.ArgumentParser(prog="birthday-reminder", description="Birthday Reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", description="Just read file and check for errors")
    show_parser = subparsers.add_parser("show", description="Show birthdays from file")
    gshow_parser = subparsers.add_parser("gshow", description="Show birthdays from Google Calendar")
    diff_parser = subparsers.add_parser("diff", description="Show differences between file and Google Calendar")
    upload_parser = subparsers.add_parser("upload", description="Upload birthdays from file to Google Calendar")

    for subparser in [show_parser, gshow_parser]:
        subparser.add_argument("sort_type", choices=[t.value for t in list(BirthdayEvent.SortTypes)])

    for subparser in [validate_parser, show_parser, diff_parser, upload_parser]:
        subparser.add_argument("file_path", type=str, help="Path to the file with birthdays")

    upload_parser.add_argument(
        "-f", "--force", action="store_true", help="Force upload even if there are no differences"
    )
    upload_parser.add_argument("-y", "--yes", action="store_true", help="Do not ask for confirmation")

    for subparser in [validate_parser, show_parser, gshow_parser, diff_parser, upload_parser]:
        subparser.add_argument("-v", "--verbose", action="count", default=0)
        for key, value in config.get_public_vars().items():
            if key != "verbose":
                subparser.add_argument(
                    f"--{key.replace('_', '-')}",
                    type=type(value),
                )
    args = parser.parse_args()
    args_dict = vars(args)

    args_dict_for_config = copy.deepcopy(args_dict)
    for key in ["command", "sort_type", "file_path", "force", "yes"]:
        args_dict_for_config.pop(key, None)
    args_dict_no_nones = {k: v for k, v in args_dict_for_config.items() if v is not None}
    try:
        config.set_public_vars(args_dict_no_nones)
    except Exception as e:
        print(Colorize.fail(e))
        exit(1)
    if config.verbose:
        print(f"Configuration:\n---\n{yaml.dump(config.get_public_vars())}---")

    if "file_path" in args_dict:
        try:
            reader = FileReader(config, args.file_path)
            file_events = reader.events
        except Exception as e:
            print(Colorize.fail(e))
            exit(2)

    if args.command in ["gshow", "diff", "upload"]:
        try:
            gc_api = GoogleCalendarApi(config)
            google_events = gc_api.get_events()
        except Exception as e:
            print(Colorize.fail(e))
            exit(3)

    match args.command:
        case "validate":
            print(Colorize.success(f"File {args.file_path} is valid!"))
            exit(0)
        case "show":
            show(file_events, BirthdayEvent.SortTypes(args.sort_type))
        case "gshow":
            show(google_events, BirthdayEvent.SortTypes(args.sort_type))
        case "diff":
            diff(config, file_events=file_events, google_events=google_events)
        case "upload":
            print("---------------------------------")
            diffs_num = diff(config, file_events=file_events, google_events=google_events)
            print("---------------------------------")

            if diffs_num == 0 and not args.force:
                print(Colorize.success("No differences found. Nothing to upload. Exiting."))
                exit(0)

            print(
                Colorize.warning(
                    f"Do you want to upload events from file to Google Calendar?\n"
                    f"All events in '{config.calendar_name}' calendar will be deleted "
                    f"and replaced with events from file."
                )
            )

            if not args.yes:
                while True:
                    user_input = input(
                        Colorize.warning("Press 'y' to continue or 'n' to cancel, then press 'Enter':")
                    ).lower()
                    if user_input not in ["y", "n"]:
                        print(Colorize.fail("Invalid input. Please try again."))
                        continue
                    break
                if user_input == "n":
                    print(Colorize.warning("Upload cancelled."))
                    exit(0)

            try:
                gc_api = GoogleCalendarApi(config)
                gc_api.delete_all_events(google_events)
                gc_api.upload_events(file_events)
            except Exception as e:
                print(Colorize.fail(e))
                exit(15)
            print(Colorize.success("Events uploaded successfully!"))
