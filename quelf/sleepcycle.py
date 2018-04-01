import json
import re
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)
from zipfile import ZipFile

import pandas as pd
import progressbar
import requests
from mypy_extensions import TypedDict

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
    def last_sleepsession_id(self) -> int:
        """Return the session ID of the latest recorded sleep data."""
        if not hasattr(self, '_last_sleepsession_id'):
            self.persist_first_and_last_sleepsession_id()
        return self._last_sleepsession_id

    @property
    def first_sleepsession_id(self) -> int:
        """Return the session ID of the latest recorded sleep data."""
        if not hasattr(self, '_first_sleepsession_id'):
            self.persist_first_and_last_sleepsession_id()
        return self._first_sleepsession_id

    def persist_first_and_last_sleepsession_id(self) -> None:
        """Fetch and persist the first and last sleepsession IDs."""
        landing_page = self.session.get(BASE_URL + '/site/comp/totalstat').text
        self._first_sleepsession_id: int = int(re.search(
            r'var first_sleepsession_id = \'(\d+)\'',
            landing_page,
        ).group(1))
        self._last_sleepsession_id: int = int(re.search(
            r'var last_sleepsession_id = \'(\d+)\'',
            landing_page,
        ).group(1))

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


class SleepSessionJSON(TypedDict):
    rating: int                         # 0-3
    heartrate: Union[str, List[float]]  # "n/a" is None
    graph_date: str                     # "Monday 14-15 Dec, 2015"
    stop_tick_tz: str                   # "Europe/Oslo"
    start_tick_tz: str                  # "Europe/Oslo"
    window_offset_stop: str             # "2015-12-15T07:25:00"
    stop_tick: float                    # 471853567.05131602
    start_global: str                   # "2015-12-14T22:11:58"
    id: int                             # 5029422020165632
    window_start: str                   # "2015-12-15T07:07:25:00",
    window_offset_start: str            # "2015-12-15T07:07:25:00",
    stop_global: str                    # "2015-12-15T06:06:26:07"
    stop_local: str                     # "2015-12-15T07:07:26:07"
    stats_version: int                  # 1
    sleep_notes: Union[str, List[str]]  # "n/a" is None
    graph: List[Tuple[int, float]]      # [index, activity_level]
    stats_sq: float                     # [0.0, 1.0]
    seconds_from_gmt: int               # 3600
    alarm_mode: int                     # 0 or 1
    xaxis: List[Tuple[float, str]]      # [70.626328038045131, "05"]
    graph_tib: str                      # "8:14"
    start_tick: float                   # 471823918.51976001
    stats_wakeup: int                   # 0 or 1
    stats_duration: float               # 29648.53155601025
    stats_sol: int                      # 0 or 1
    stats_mph: float                    # 2.8861129111405419
    window_stop: str                    # "2015-12-15T07:25:00"
    state_mode: int                     # 2
    graph_indbed: str                   # "23:11 - 07:26"
    steps: str                          # "4261 steps"
    start_local: str                    # "2015-12-14T23:11:58"


class SleepSessionsCache:
    """SleepSession JSON objects persisted to disk."""
    DEFAULT_PATH = DATA_DIRECTORY / 'sleep_sessions.json'

    def __init__(self, json_file: Path = DEFAULT_PATH) -> None:
        """Initialize a cache persisted to `json_file`."""
        self.path = json_file

        if not self.path.is_file():
            # No sleep sessions have been cached, so we need to create an empty
            # cache file
            self.memory = {}
            with open(self.path, 'w') as cache_file:
                json.dump({}, cache_file)
        else:
            # There are existing cached sleep sessions. We need to import them
            # into memory, and cast string indeces to integer values, as JSON
            # does not support integer indexes in dictionaries.
            with open(self.path, 'r') as cache_file:
                content = json.load(cache_file)
                self.memory = {
                    int(session_id): sleep_session
                    for session_id, sleep_session
                    in content.items()
                    if session_id not in ('newest_session_id', 'first_session_id',)
                }
                self.memory['newest_session_id'] = int(content['newest_session_id'])
                self.memory['first_session_id'] = int(content['first_session_id'])

    def __setitem__(
        self,
        session_id: int,
        sleep_session: SleepSessionJSON,
    ) -> None:
        """Insert a new sleep session into the cache."""
        assert session_id not in self.memory

        self.memory[session_id] = sleep_session
        self.memory['newest_session_id'] = session_id
        if 'first_session_id' not in self.memory:
            self.memory['first_session_id'] = session_id

        with open(self.path, 'w') as cache_file:
            json.dump(self.memory, cache_file)

    @property
    def newest(self) -> Optional[SleepSessionJSON]:
        """Return the most recently inserted sleep session."""
        try:
            return self.memory[self.memory['newest_session_id']]
        except KeyError:
            return None

    @property
    def first(self) -> Optional[SleepSessionJSON]:
        """Return the first inserted sleep session."""
        try:
            return self.memory[self.memory['first_session_id']]
        except KeyError:
            return None

    def __getitem__(self, session_id: int) -> SleepSessionJSON:
        """Retrieve sleep session from cache."""
        return self.memory[session_id]

    def __contains__(self, session_id: int) -> bool:
        """Return True if `session_id` has been persisted to cache."""
        return session_id in self.memory

    def __repr__(self) -> str:
        return f'<SleepSessionsCache: length={len(self.memory)}>'


class SleepSessions:
    def __init__(
        self,
        first_sleepsession_id: int,
        last_sleepsession_id: int,
        session: requests.Session,
    ) -> None:
        self.first_sleepsession_id = first_sleepsession_id
        self.last_sleepsession_id = last_sleepsession_id
        self.session = session
        self.cache = SleepSessionsCache()


    def __iter__(self) -> 'SleepSessions':
        """Return Iterator which iterates over all sleep sessions."""
        return self

    def __next__(self) -> SleepSessionJSON:
        """Fetch next sleep session JSON from SleepSecure(TM) endpoint."""
        if not hasattr(self, 'current_sleepsession_id'):
            self.current_sleepsession_id = self.first_sleepsession_id
            return self.sleep_session(session_id=self.current_sleepsession_id)
        else:
            try:
                current_sleepsession = self.sleep_session(
                    session_id=self.current_sleepsession_id,
                    previous=True,
                )
                self.current_sleepsession_id = current_sleepsession['id']
                return current_sleepsession
            except ValueError:
                raise StopIteration()

    def sleep_session(
        self,
        session_id: int,
        next_: bool = False,
        previous: bool = False,
    ) -> SleepSessionJSON:
        """
        Return SleepSessionJSON for specific id.

        `next_` and `previous` flags indicate getting the next/previous
        available sleepsession.
        """
        params = {'id': str(session_id)}
        if next_:
            params['next'] = '1'
        elif previous:
            params['prev'] = '1'
        elif session_id in self.cache:
            return self.cache[session_id]

        try:
            session_response = self.session.get(
                BASE_URL + '/stat/session',
                params=params,
            ).json()

            if session_response['id'] not in self.cache:
                self.cache[session_response['id']] = session_response

            return session_response
        except json.decoder.JSONDecodeError:
            if next_:
                raise ValueError('No next sleepsession')
            elif previous:
                raise ValueError('No previous sleepsession')
            else:
                raise
