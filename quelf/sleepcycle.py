from pathlib import Path
from typing import Dict
import re
from zipfile import ZipFile

import pandas as pd
import requests

from .config import Config, DATA_DIRECTORY

BASE_URL = 'https://s.sleepcycle.com'
SLEEP_CYCLE_LOGIN_URL = BASE_URL + '/site/login'
SLEEP_CYCLE_DATA_URL = BASE_URL + '/export/original'

ZIP_FILE = DATA_DIRECTORY / 'sleepcycle_data.zip'
JSON_FILE = DATA_DIRECTORY / 'data_json.txt'


class SleepCycle:
    def __init__(self) -> None:
        self.zip_data_path = ZIP_FILE
        self.json_data_path = JSON_FILE

    @property
    def session(self) -> requests.Session:
        """Requests Session authenticated against SleepSecure."""
        if hasattr(self, '_session'):
            return self._session

        conf = Config()['sleepcycle']
        email = conf['email']
        password = conf['password']
        self.headers = {'username': email, 'password': password}

        self._session: requests.Session = requests.Session()
        self._session.get(SLEEP_CYCLE_LOGIN_URL)
        self._session.post(
            SLEEP_CYCLE_LOGIN_URL,
            data=self.headers,
        )

        self.headers['Cookies'] = "; ".join(
            [
                str(key) + "=" + str(value)
                for key, value
                in self._session.cookies.items()
            ],
        )

        return self._session

    @property
    def last_sleepsession_id(self) -> str:
        """Return the session ID of the latest recorded sleep data."""
        if not hasattr(self, '_last_sleepsession_id'):
            self.persist_first_and_last_sleepsession_id()
        return self._last_sleepsession_id

    @property
    def first_sleepsession_id(self) -> str:
        """Return the session ID of the latest recorded sleep data."""
        if not hasattr(self, '_first_sleepsession_id'):
            self.persist_first_and_last_sleepsession_id()
        return self._first_sleepsession_id

    def persist_first_and_last_sleepsession_id(self) -> None:
        """Fetch and persist the first and last sleepsession IDs."""
        landing_page = self.session.get(BASE_URL + '/site/comp/totalstat').text
        self._first_sleepsession_id: str = re.search(
            r'var first_sleepsession_id = \'(\d+)\'',
            landing_page,
        ).group(1)
        self._last_sleepsession_id: str = re.search(
            r'var last_sleepsession_id = \'(\d+)\'',
            landing_page,
        ).group(1)

    def download_data(self) -> None:
        """Download the latest SleepCycle data to the data directory."""
        response = self.session.get(SLEEP_CYCLE_DATA_URL, stream=True)
        assert response.status_code == 200

        with open(self.zip_data_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=512):
                if chunk:  # filter out keep-alive new chunks
                    handle.write(chunk)

    def unzip_data(self) -> None:
        """Unzip exported data."""
        if not ZIP_FILE.is_file():
            self.download_data()

        with ZipFile(ZIP_FILE, 'r') as zip_file:
            zip_file.extractall(DATA_DIRECTORY)

    def load_json(self) -> pd.DataFrame:
        """Load exported JSON file into pandas DataFrame."""
        if not JSON_FILE.is_file():
            self.unzip_data()

        return pd.read_json(
            path_or_buf=JSON_FILE,
            orient='records',
            convert_dates=['start', 'stop'],
        )

    @property
    def data(self) -> pd.DataFrame:
        """Return data from 'export' functionality of SleepSecure(TM)."""
        if not hasattr(self, '_data'):
            self._data = self.load_json()

        return self._data

    def fetch(self, endpoint: str, params: Dict = {}) -> Dict:
        """Fetch JSON from SleepSecure(TM) endpoint."""
        return self.session.get(BASE_URL + endpoint, params=params).json()
