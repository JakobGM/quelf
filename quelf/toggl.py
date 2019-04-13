from typing import Dict

import requests
from requests.auth import HTTPBasicAuth

from .config import config


TOGGL_BASE_URL = 'https://toggl.com/reports/api/v2'


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
