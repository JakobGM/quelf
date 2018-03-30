import os

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
