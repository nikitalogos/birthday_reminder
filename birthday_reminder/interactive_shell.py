import traceback

from utils.colorize import Colorize

from birthday_reminder.app import main

if __name__ == "__main__":
    print(
        Colorize.info(
            "Welcome to the Birthday Reminder Interactive Shell!\n"
            "Type '-h' or '--help' for help\n"
            "Type '<command> -h' for help with command (ex. 'show -h')\n"
        )
    )

    while True:
        args = input("birthday-reminder ")
        try:
            main(args.split())
        except SystemExit:
            pass  # argparse exits with 0 on --help
        except Exception:
            traceback.print_exc()
