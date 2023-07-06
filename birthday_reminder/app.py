import argparse
import copy
import traceback
from typing import Optional

from birthday_reminder.birthday_event import BirthdayEvent, ComparisonResult, compare_events_file_and_google
from birthday_reminder.configs.base_config import add_arguments_to_parser
from birthday_reminder.configs.main_config import MAIN_CONFIG_FILE, MainConfig
from birthday_reminder.drivers.file_reader import FileReader
from birthday_reminder.drivers.google_calendar_api import GoogleCalendarApi
from birthday_reminder.utils.colorize import Colorize


def print_events(events: list[BirthdayEvent]):
    chars_for_digit = len(str(len(events)))
    for idx, event in enumerate(events):
        print(f"{(idx + 1):{chars_for_digit}}. {event}")
    print()


def show(events: list[BirthdayEvent], sort_type: BirthdayEvent.SortTypes):
    messages = {
        BirthdayEvent.SortTypes.year: "year of birth",
        BirthdayEvent.SortTypes.date: "month and day of birth",
        BirthdayEvent.SortTypes.next: "days to the next birthday",
    }
    message = Colorize.info(f"\nShowing birthdays sorted by {messages[sort_type]}:\n")
    print(message)

    events_sorted = BirthdayEvent.sort_events(events, sort_type)
    print_events(events_sorted)


def print_diff(
    file_events: list[BirthdayEvent], google_events: list[BirthdayEvent], r: ComparisonResult, config: MainConfig
):
    print(
        Colorize.info(
            f"File has {len(file_events)} events, Google Calendar has {len(google_events)} events.\n"
            f"{len(r.equal_events)} events are equal,\n"
            f"{len(r.updated_events)} events are updated,\n"
            f"{len(r.file_only_events)} events are only in file,\n"
            f"{len(r.google_only_events)} events are only in Google Calendar.\n"
        )
    )
    if config.verbose and len(r.equal_events) > 0:
        print(Colorize.info("Equal events:"))
        print_events(list(r.equal_events))
    if len(r.updated_events) > 0:
        print(Colorize.warning("Updated events:"))
        print_events(list(r.updated_events))
    if len(r.file_only_events) > 0:
        print(Colorize.warning("Events only in file:"))
        print_events(list(r.file_only_events))
    if len(r.google_only_events) > 0:
        print(Colorize.warning("Events only in Google Calendar:"))
        print_events(list(r.google_only_events))


def print_error(args, e: Exception):
    print(Colorize.fail(str(e)))
    if args.verbose >= 3:
        traceback.print_exc()


def main(cmdline_args: Optional[list] = None) -> int:
    config = MainConfig()

    parser = argparse.ArgumentParser(prog="birthday-reminder", description="Birthday Reminder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", description="Just read file and check for errors")
    show_parser = subparsers.add_parser("show", description="Show birthdays from file")
    gshow_parser = subparsers.add_parser("gshow", description="Show birthdays from Google Calendar")
    diff_parser = subparsers.add_parser("diff", description="Show differences between file and Google Calendar")
    upload_parser = subparsers.add_parser("upload", description="Upload birthdays from file to Google Calendar")

    for subparser in [show_parser, gshow_parser]:
        subparser.add_argument("sort_type", choices=[t for t in BirthdayEvent.SortTypes])

    for subparser in [validate_parser, show_parser, diff_parser, upload_parser]:
        subparser.add_argument("-i", "--input-file", type=str, help="Path to the file with birthdays")

    upload_parser.add_argument(
        "-f", "--force", action="store_true", help="Force upload even if there are no differences"
    )
    upload_parser.add_argument("-y", "--yes", action="store_true", help="Do not ask for confirmation")

    for subparser in [validate_parser, show_parser, gshow_parser, diff_parser, upload_parser]:
        subparser.add_argument("-v", "--verbose", action="count", default=0, help="Display more information")
        subparser.add_argument("-c", "--config-file", type=str, help="Path to the config file")
        add_arguments_to_parser(subparser, config, exclude_params=["verbose", "input_file"])

    args = parser.parse_args(args=cmdline_args)
    args_dict = vars(args)

    # update config
    if args.verbose >= 2:
        print(Colorize.info("Initial config:"))
        print(config)

    args_dict_for_config = copy.deepcopy(args_dict)
    for key in ["config_file", "command", "sort_type", "force", "yes"]:
        args_dict_for_config.pop(key, None)
    args_dict_no_nones = {k: v for k, v in args_dict_for_config.items() if v is not None}
    try:
        if args.config_file is not None:
            if args.verbose >= 2:
                print(Colorize.info(f"config_file provided. Loading config from file: {args.config_file}"))
            config.set_file_path(args.config_file)
            config.load_from_file()
            if args.verbose >= 2:
                print(config)
        else:
            if args.verbose >= 2:
                print(Colorize.info("config_file not provided. Using default config_file path."))
            config.set_file_path(MAIN_CONFIG_FILE)
            config.load_from_file()
            if args.verbose >= 2:
                print(config)

        if len(args_dict_no_nones) > 0:
            if args.verbose >= 2:
                print(Colorize.info(f"Updating config with provided command line arguments:\n{args_dict_no_nones}"))
            config.set_public_vars(args_dict_no_nones)
            if args.verbose >= 2:
                print(config)
    except Exception as e:
        print_error(args, e)
        return 1
    if config.verbose:
        print(Colorize.info("Final configuration:"))
        print(config)
    # end update config

    if args.command in ["validate", "show", "diff", "upload"]:
        try:
            reader = FileReader(config)
            file_events = reader.events
        except Exception as e:
            print_error(args, e)
            return 2

    if args.command in ["gshow", "diff", "upload"]:
        try:
            gc_api = GoogleCalendarApi(config)
            google_events = gc_api.get_events()
        except Exception as e:
            print_error(args, e)
            return 3

    match args.command:
        case "validate":
            print(Colorize.success(f"File {config.input_file} is valid!"))
            return 0
        case "show":
            show(file_events, BirthdayEvent.SortTypes(args.sort_type))
        case "gshow":
            show(google_events, BirthdayEvent.SortTypes(args.sort_type))
        case "diff":
            cmp_result = compare_events_file_and_google(file_events=file_events, google_events=google_events)
            print_diff(file_events, google_events, cmp_result, config)
        case "upload":
            cmp_result = compare_events_file_and_google(file_events=file_events, google_events=google_events)
            print("---------------------------------")
            print_diff(file_events, google_events, cmp_result, config)
            print("---------------------------------")

            if args.force:
                print(
                    Colorize.warning(
                        "Performing force upload.\n"
                        f"All events in '{config.calendar_name}' calendar will be deleted "
                        f"and replaced with events from file."
                    )
                )
                try:
                    gc_api.delete_events(google_events)
                    gc_api.create_events(file_events)
                except Exception as e:
                    print_error(args, e)
                    return 11
                print(Colorize.success("Events uploaded successfully!"))
                return 0

            if not cmp_result.has_changes:
                print(Colorize.success("No differences found. Nothing to upload. Exiting."))
                return 0
            else:
                changes_str = (
                    f"{len(cmp_result.google_only_events)} events will be deleted,\n"
                    f"{len(cmp_result.updated_events)} events will be updated,\n"
                    f"{len(cmp_result.file_only_events)} events will be created."
                )

                if not args.yes:
                    print(
                        Colorize.warning("Do you want to upload events from file to Google Calendar?\n" + changes_str)
                    )
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
                        return 0

                try:
                    google_events_aligned = []
                    file_events_aligned = []

                    def check_duplicates(events, target: str):
                        """This should never happen because duplicates checks are performed before"""
                        duplicate_events_str = "\n".join([str(e) for e in events])
                        assert len(events) == 1, (
                            f"{target} contains duplicates, updating is not possible.\n"
                            f"\nDuplicate events:\n{duplicate_events_str}"
                        )

                    for updated_event in cmp_result.updated_events:
                        events = [e for e in google_events if e == updated_event]
                        check_duplicates(events, "Google Calendar")
                        google_events_aligned += events

                        events = [e for e in file_events if e == updated_event]
                        check_duplicates(events, "File")
                        file_events_aligned += events

                    gc_api.delete_events(google_events=[e for e in google_events if e in cmp_result.google_only_events])
                    gc_api.update_events(file_events=file_events_aligned, google_events=google_events_aligned)
                    gc_api.create_events(file_events=[e for e in file_events if e in cmp_result.file_only_events])
                except Exception as e:
                    print_error(args, e)
                    return 12
                print(Colorize.success("Events uploaded successfully!"))
                return 0

            assert False, "Unreachable code"
    return 0
