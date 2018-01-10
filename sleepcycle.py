import requests

from config import Config

SLEEP_CYCLE_LOGIN_URL = 'https://s.sleepcycle.com/site/login'
SLEEP_CYCLE_DATA_URL = 'https://s.sleepcycle.com/export/original'


class SleepCycle():
    def __init__(self) -> None:
        self.zip_data_path = 'data/sleepcycle_data.zip'

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

