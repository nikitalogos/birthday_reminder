import json
import os.path

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from ..configs.main_config import MainConfig


class GoogleApiAuth:
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    def __init__(self, secret_file: str = ".auth/google_secret.json", token_file: str = ".auth/google_token.json"):
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
    base_url = "https://www.googleapis.com/calendar/v3"

    def __init__(self, config: MainConfig):
        self.config = config

        self.token = GoogleApiAuth().token

        self._headers = {"Authorization": "Bearer {}".format(self.token)}

    def _request(self, url: str, method: str = "GET", data: dict | None = None) -> dict:
        url = self.base_url + url
        r = requests.request(method, url, headers=self._headers, data=data)
        return r.json()

    def get_calendars(self) -> dict:
        return self._request("/users/me/calendarList")
