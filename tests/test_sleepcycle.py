import os

import pandas as pd
import pytest

from quelf.sleepcycle import JSON_FILE, ZIP_FILE, SleepCycle


@pytest.mark.skipif(ZIP_FILE.is_file(), reason='Data already downloaded')
def test_downloading_data_from_sleepcycle():
    sc = SleepCycle()
    sc.download_data()
    assert ZIP_FILE.is_file()


@pytest.mark.skipif(JSON_FILE.is_file(), reason='Data already unzipped')
def test_extraction_of_json_file():
    sc = SleepCycle()
    sc.unzip_data()
    assert JSON_FILE.is_file()


def test_importing_json_from_downloaded_data():
    sc = SleepCycle()
    data = sc.load_json()
    assert isinstance(data, pd.DataFrame)


def test_lazily_loaded_data_attribute():
    sc = SleepCycle()
    assert not hasattr(sc, '_data')

    data = sc.data
    assert hasattr(sc, '_data')


def test_getting_latest_sleep_session_id():
    sc = SleepCycle()
    assert int(sc.last_sleepsession_id) > 0


def test_getting_first_sleep_session_id():
    sc = SleepCycle()
    assert int(sc.first_sleepsession_id) > 0
