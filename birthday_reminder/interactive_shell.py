import traceback

from birthday_reminder.app import main

if __name__ == "__main__":
    while True:
        args = input("birthday-reminder ")
        try:
            main(args.split())
        except Exception:
            traceback.print_exc()
