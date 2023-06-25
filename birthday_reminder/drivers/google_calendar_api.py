import json
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..configs.main_config import MainConfig


class GoogleApiAuth:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    _PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    _DEFAULT_SECRET_FILE = os.path.join(_PROJECT_DIR, ".auth/google_secret.json")
    _DEFAULT_TOKEN_FILE = os.path.join(_PROJECT_DIR, ".auth/google_token.json")

    def __init__(self, secret_file: str = _DEFAULT_SECRET_FILE, token_file: str = _DEFAULT_TOKEN_FILE):
        self.secret_file = secret_file
        self.token_file = token_file

        self.creds = self._authorize()

    def _load_secret_info(self) -> dict:
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
                creds = flow.run_local_server(port=58585)

            self._save_token(creds)
        return creds

    @property
    def token(self) -> str:
        return self.creds.token


class GoogleCalendarApi:
    def __init__(self, config: MainConfig):
        self.config = config

        creds = GoogleApiAuth().creds
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
            # 'colorId': str(self.config.calendar_color_id),  # todo doesn't work
            # todo add defaultReminders
        }

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

    def get_all_events(self):
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
        return events
