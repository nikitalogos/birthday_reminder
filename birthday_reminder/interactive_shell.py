import traceback

from birthday_reminder.app import main

if __name__ == "__main__":
    while True:
        args = input("birthday-reminder ")
        try:
            main(args.split())
        except SystemExit:
            pass  # argparse exits with 0 on --help
        except Exception:
            traceback.print_exc()
