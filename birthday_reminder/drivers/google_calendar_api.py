import enum
import json
import os.path
import sys
import time
from typing import Iterable

import tqdm
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from birthday_reminder.birthday_event import BirthdayEvent, BirthdayEventSignature
from birthday_reminder.configs.main_config import MainConfig
from birthday_reminder.utils.colorize import Colorize


class GoogleApiAuth:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    if getattr(sys, "frozen", False):
        # Running as a frozen executable
        _PROJECT_DIR = os.path.dirname(sys.executable)
    else:
        # Running in a development environment
        _PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    _DEFAULT_SECRET_FILE = os.path.join(_PROJECT_DIR, "auth", "google_secret.json")
    _DEFAULT_TOKEN_FILE = os.path.join(_PROJECT_DIR, "auth", "google_token.json")

    def __init__(self, port: int, secret_file: str = _DEFAULT_SECRET_FILE, token_file: str = _DEFAULT_TOKEN_FILE):
        self.port = port
        self.secret_file = secret_file
        self.token_file = token_file

        self.creds = self._authorize()

    def _load_secret_info(self) -> dict:
        if not os.path.exists(self.secret_file):
            raise FileNotFoundError(
                f'Google secret file not found at "{self.secret_file}"!\n'
                + Colorize.warning(
                    "It seems that you executed command that requires authorization in Google Api.\n"
                    "To learn how to authorize, read the README.md:\n"
                )
                + Colorize.info(
                    "https://github.com/nikitalogos/birthday_reminder/tree/main#authorize-in-google-calendar-api"
                )
            )
        with open(self.secret_file) as f:
            return json.load(f)

    def _load_token(self) -> Credentials | None:
        if not os.path.exists(self.token_file):
            return None
        with open(self.token_file) as f:
            return Credentials.from_authorized_user_info(json.load(f))

    def _save_token(self, creds: Credentials):
        with open(self.token_file, "w") as f:
            json.dump(json.loads(creds.to_json()), f)

    def _authorize(self) -> Credentials:
        creds = self._load_token()

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                secret_info = self._load_secret_info()
                flow = InstalledAppFlow.from_client_config(client_config=secret_info, scopes=self.SCOPES)
                creds = flow.run_local_server(port=self.port)

            self._save_token(creds)
        return creds

    @property
    def token(self) -> str:
        return self.creds.token


class GoogleCalendarApi:
    def __init__(self, config: MainConfig):
        self.config = config

        creds = GoogleApiAuth(config.google_oauth_port).creds
        self.service = build("calendar", "v3", credentials=creds)

        self.br_calendar = self._create_br_calendar_if_not_exist()

    def _get_calendars(self) -> dict:
        return self.service.calendarList().list().execute()

    def _create_br_calendar_if_not_exist(self):
        name = self.config.calendar_name
        br_calendar = None

        calendars = self._get_calendars()
        for calendar in calendars["items"]:
            if calendar["summary"] == name:
                print(f"Calendar '{name}' already exists")
                br_calendar = calendar
                break

        calendar_prefs = {
            "summary": self.config.calendar_name,
            # unfortunately, setting 'colorId' doesn't work
            # 'defaultReminders' also doesn't work. It's a bug in Google Api.
        }

        if self.config.verbose:
            print("---\nbr_calendar:\n" + json.dumps(br_calendar, indent=4))
            print("---\ncalendar_prefs:\n" + json.dumps(calendar_prefs, indent=4))
            print("---\n")

        if br_calendar is None:
            print(f"Creating calendar '{name}'...")
            return self.service.calendars().insert(body=calendar_prefs).execute()
        else:
            for k, v in calendar_prefs.items():
                if br_calendar[k] != v:
                    print(f"Updating calendar '{name}'...")
                    br_calendar.update(calendar_prefs)
                    return self.service.calendars().update(calendarId=br_calendar["id"], body=br_calendar).execute()
        return br_calendar

    def _get_all_events(self) -> list[dict]:
        events = []
        page_token = None
        while True:
            result = (
                self.service.events()
                .list(
                    calendarId=self.br_calendar["id"],
                    singleEvents=False,
                    pageToken=page_token,
                    maxResults=2500,
                )
                .execute()
            )
            events.extend(result.get("items", []))

            page_token = result.get("nextPageToken")
            if not page_token:
                break

        # although we set cancelledEvents=False, we still can get cancelled events
        # if they are exceptions of a recurring event.
        # In our app user is not expected to modify any events manually, but he can.
        events = list(filter(lambda event: event["status"] != "cancelled", events))

        return events

    def get_events(self) -> list[BirthdayEvent]:
        events = []
        google_events = self._get_all_events()

        for google_event in google_events:
            events.append(BirthdayEvent.from_google_event(google_event))
        return events

    @enum.unique
    class EventActions(enum.Enum):
        CREATE = enum.auto()
        UPDATE = enum.auto()
        DELETE = enum.auto()

    def _process_one_event(self, google_event: dict, action: EventActions):
        delays = [1, 2, 4, 8, 16, 32, 64, 128]

        for n in range(len(delays)):
            try:
                match action:
                    case self.EventActions.CREATE:
                        self.service.events().insert(calendarId=self.br_calendar["id"], body=google_event).execute()
                    case self.EventActions.UPDATE:
                        self.service.events().update(
                            calendarId=self.br_calendar["id"], eventId=google_event["id"], body=google_event
                        ).execute()
                    case self.EventActions.DELETE:
                        self.service.events().delete(
                            calendarId=self.br_calendar["id"], eventId=google_event["id"]
                        ).execute()
                break
            except Exception as e:
                # if user creates exception from recurring event, it will cause 410 error
                # if exception event will be deleted after base event
                if type(e) is HttpError and e.resp.status == 410:
                    print(
                        f"Event has been deleted. Probably exception from a recurring event. "
                        f"Ignoring this error.\n{google_event=}"
                    )
                    break

                if n == len(delays) - 1:
                    raise Exception(f"Request failed with {e}\nFailed to delete event! {google_event=}")
                print(f"Request failed with {e}, retrying in {delays[n]} seconds...")
                time.sleep(delays[n])

    def _create_one_event(self, google_event: dict):
        self._process_one_event(google_event, self.EventActions.CREATE)

    def _update_one_event(self, google_event: dict):
        self._process_one_event(google_event, self.EventActions.UPDATE)

    def _delete_one_event(self, google_event: dict):
        self._process_one_event(google_event, self.EventActions.DELETE)

    def create_events(self, file_events: Iterable[BirthdayEvent]):
        for event in tqdm.tqdm(file_events, desc="Creating events in Google Calendar"):
            self._create_one_event(event.to_google_event())

    def update_events(self, file_events: list[BirthdayEvent], google_events: list[BirthdayEvent]):
        assert all(
            BirthdayEventSignature.from_event(file_events[i]) == BirthdayEventSignature.from_event(google_events[i])
            for i in range(len(file_events))
        ), "Expected list of corresponding events"

        new_events = []
        for idx in range(len(file_events)):
            new_event = file_events[idx].to_google_event()
            new_event["id"] = google_events[idx].google_event["id"]  # type: ignore # raising exception if None is ok
            new_events.append(new_event)

        for new_event in tqdm.tqdm(new_events, desc="Updating events in Google Calendar"):
            self._update_one_event(new_event)

    def delete_events(self, google_events: Iterable[BirthdayEvent]):
        assert all(
            event.google_event is not None for event in google_events
        ), "All events must have 'google_event' attribute"

        for event in tqdm.tqdm(google_events, desc="Deleting events from Google Calendar"):
            self._delete_one_event(event.google_event)  # type: ignore # mypy doesn't see assert above
