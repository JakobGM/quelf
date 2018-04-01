import os
from pathlib import Path

import pandas as pd
import pytest

from quelf.sleepcycle import (
    CachedSleepSessions,
    JSON_FILE,
    ZIP_FILE,
    SleepCycle,
    SleepSessions,
)


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
    assert sc.last_sleepsession_id > 0


def test_getting_first_sleep_session_id():
    sc = SleepCycle()
    assert sc.first_sleepsession_id > 0


@pytest.fixture
def cached_sleep_sessions(tmpdir):
    cache_path = Path(tmpdir) / 'cache.json'
    return CachedSleepSessions(json_file=cache_path)


class TestCachedSleepSessions:
    def test_creation_of_cached_sleep_session_file(self, cached_sleep_sessions):
        assert cached_sleep_sessions.path.is_file()

    def test_initial_content_being_empty_dict(self, cached_sleep_sessions):
        with open(cached_sleep_sessions.path, 'r') as cache:
            content = json.load(cache)
            assert content == {}

    def test_inserting_content(self, cached_sleep_sessions):
        cached_sleep_sessions[24] = '2'
        assert cached_sleep_sessions[24] == '2'

    def test_in_keyword(self, cached_sleep_sessions):
        assert 24 not in cached_sleep_sessions

        cached_sleep_sessions[24] = '2'
        assert 24 in cached_sleep_sessions

    def test_persistence_to_disk(self, cached_sleep_sessions):
        cached_sleep_sessions[24] = '2'
        with open(cached_sleep_sessions.path, 'r') as cache:
            content = json.load(cache)
            assert content == {'24': '2'}

        cached_sleep_sessions[1] = {'test': 'value'}
        with open(cached_sleep_sessions.path, 'r') as cache:
            content = json.load(cache)
            assert content == {'24': '2', '1': {'test': 'value'}}

        cache_path = cached_sleep_sessions.path
        del cached_sleep_sessions
        new_cached_sleep_sessions = CachedSleepSessions(json_file=cache_path)
        assert new_cached_sleep_sessions[24] == '2'
        assert new_cached_sleep_sessions[1] == {'test': 'value'}


@pytest.fixture
def sleep_sessions():
    sc = SleepCycle()
    return SleepSessions(
        first_sleepsession_id=sc.first_sleepsession_id,
        last_sleepsession_id=sc.last_sleepsession_id,
        session=sc.session,
    )


class TestSleepSessions:
    def test_iterating_over_the_first_sleepsessions(self, sleep_sessions):
        first_sleepsession = next(sleep_sessions)
        assert sleep_sessions.first_sleepsession_id == first_sleepsession['id']

        second_sleepsession = next(sleep_sessions)
        assert first_sleepsession['id'] != second_sleepsession['id']
