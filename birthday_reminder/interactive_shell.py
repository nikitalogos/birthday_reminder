import traceback

from birthday_reminder.app import main
from birthday_reminder.utils.colorize import Colorize

if __name__ == "__main__":
    print(
        Colorize.info(
            "Welcome to the Birthday Reminder Interactive Shell!\n"
            "To list available commands, type '-h', then press Enter\n"
            "To learn how to use the command, type '<command> -h' (ex. 'show -h'), then press Enter\n"
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
