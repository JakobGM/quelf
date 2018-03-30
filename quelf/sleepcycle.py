import json
from pathlib import Path
from zipfile import ZipFile

import pandas as pd
import requests

from .config import Config, DATA_DIRECTORY

SLEEP_CYCLE_LOGIN_URL = 'https://s.sleepcycle.com/site/login'
SLEEP_CYCLE_DATA_URL = 'https://s.sleepcycle.com/export/original'
ZIP_FILE = DATA_DIRECTORY / 'sleepcycle_data.zip'
JSON_FILE = DATA_DIRECTORY / 'data_json.txt'


class SleepCycle():
    def __init__(self) -> None:
        self.zip_data_path = ZIP_FILE
        self.json_data_path = JSON_FILE

    def download_data(self) -> None:
        """Download the latest SleepCycle data to the data directory."""
        conf = Config()['sleepcycle']
        email = conf['email']
        password = conf['password']

        s = requests.Session()
        s.get(SLEEP_CYCLE_LOGIN_URL)
        s.post(
            SLEEP_CYCLE_LOGIN_URL,
            data={'username': email, 'password': password},
        )

        response = s.get(SLEEP_CYCLE_DATA_URL, stream=True)
        assert response.status_code == 200

        with open(self.zip_data_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=512):
                if chunk:  # filter out keep-alive new chunks
                    handle.write(chunk)

    def unzip_data(self) -> None:
        """Unzip downloaded data."""
        if not ZIP_FILE.is_file():
            self.download_data()

        with ZipFile(ZIP_FILE, 'r') as zip_file:
            zip_file.extractall(DATA_DIRECTORY)

    def load_json(self) -> pd.DataFrame:
        if not JSON_FILE.is_file():
            self.unzip_data()

        return pd.read_json(
            path_or_buf=JSON_FILE,
            orient='records',
            convert_dates=['start', 'stop'],
        )

    @property
    def data(self) -> pd.DataFrame:
        if not hasattr(self, '_data'):
            self._data = self.load_json()

        return self._data
