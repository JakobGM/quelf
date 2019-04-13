import datetime
import json
import time
from pathlib import Path
from typing import Dict, List

from mypy_extensions import TypedDict

import numpy as np

import progressbar

import requests
from requests.auth import HTTPBasicAuth

from .config import DATA_DIRECTORY, config


TOGGL_BASE_URL = 'https://toggl.com/reports/api/v2'


class DetailDict(TypedDict):
    """JSON dictionary for a single time entry."""

    id: int
    pid: int
    uid: int
    description: str
    start: str
    end: str
    updated: str
    dur: int
    user: str
    use_stop: bool
    project: str
    project_color: str
    project_hex_color: str


class DetailsDict(TypedDict):
    """JSON returned by Toggl details endpoint."""

    total_grand: int
    total_count: int
    per_page: int
    data: List[DetailDict]


class Toggl:
    """Class for retrieving and processing Toggl data."""

    def __init__(self) -> None:
        """Construct Toggl object. """
        conf = config['toggl']

        self.auth = HTTPBasicAuth(
            conf['api_token'],
            'api_token',
        )
        self.headers = {
            'user_agent': conf['email'],
            'workspace_id': conf['workspace_id'],
        }
        self.details_path = DATA_DIRECTORY / 'toggl' / 'details.json'
        self.details_path.parent.mkdir(parents=True, exist_ok=True)
        self.tidy_details_path = DATA_DIRECTORY / 'toggl' / 'tidy_details.json'

    def fetch(self, path: str, params: Dict[str, str] = {}) -> Dict:
        """
        Fetch data from Toggl JSON API.

        :param path: URL path to query from, e.g. '/summary'.
        :param params: Additional URL parameters to include in query.
        :return: JSON response in form of a python dictionary.
        """
        response = requests.get(
            url=TOGGL_BASE_URL + path,
            auth=self.auth,
            params={**self.headers, **params},
        )
        return response.json()

    def fetch_details(self) -> Dict:
        """
        Fetch and store all new detailed time entries.

        The result is available from self.details after invoked.
        """
        # We store the results keyed to year, then page of paginated results.
        # We prepopulate the results with earlier cached results.
        result: Dict[int, Dict[int, DetailsDict]] = self.details

        # We only start fetching for the newest year that we have previously
        # fetched.
        earliest_year = max(
            [int(year) for year in result.keys()] or [2006]
        )

        # And fetch until this year
        current_year = datetime.date.today().year

        years = progressbar.progressbar(range(earliest_year, current_year + 1))
        for year in years:
            # Sleep for one second in order to stay under Toggl rate limit
            time.sleep(1)

            # Fetch detailed time entries for entire year
            params = {'since': f'{year}-01-01', 'until': f'{year + 1}-01-01'}
            details: DetailsDict = self.fetch('/details', params=params)

            # Create the dictionary that will store all the pages for this year
            result.setdefault(str(year), {})
            result[str(year)]['1'] = details

            # Skip this year if cache total is equal to year total
            saved_count = sum(
                len(page.get('data', []))
                for page
                in result[str(year)].values()
            )
            if saved_count == details['total_count']:
                continue

            # Calculate how many pages there are in this year
            pages = int(np.ceil(details['total_count'] / details['per_page']))

            # Fetch the remaining pages
            for page in range(2, pages + 1):
                # Stay under the rate limit
                time.sleep(1)

                # Fetch and store the given page
                details = self.fetch(
                    '/details',
                    params={**params, 'page': page},
                )
                result[str(year)][str(page)] = details

        # Save the result, automatically saving to disk with the setter property
        self.details = result

    def save_tidy_details(self) -> Path:
        """
        Save details in tidy data format.

        The original details data format is optimized such that caching is easy,
        but the hierarchical nature of the dictionary is difficult to convert
        to a tidy data frame. This method exists to solve this.

        :return: Path to json file with tidy data content.
        """
        details = self.details
        tidy_data = []
        for year in details.values():
            for page in year.values():
                for time_entry in page['data']:
                    tidy_data.append(time_entry)

        self.tidy_details_path.write_text(json.dumps(tidy_data))
        return self.tidy_details_path

    @property
    def details(self) -> DetailsDict:
        """Retrieve detailed time entries."""
        try:
            return json.loads(self.details_path.read_text())
        except FileNotFoundError:
            return {}

    @details.setter
    def details(self, details: DetailsDict):
        """Save new detailed time entries, saving to disk."""
        self.details_path.write_text(json.dumps(details))
