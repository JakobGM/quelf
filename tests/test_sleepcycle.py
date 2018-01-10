import os

from sleepcycle import SleepCycle


def test_downloading_data_from_sleepcycle():
    sc = SleepCycle()
    sc.download_data()

    try:
        os.remove(sc.zip_data_path)
    except OSError:
        raise Exception("SleepCycle data has not been downloaded")

