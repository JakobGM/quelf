from matplotlib import pyplot as plt
import pandas as pd

from quelf.sleepcycle import SleepCycle

sc = SleepCycle()
sleep_data: pd.DataFrame = sc.data

time_slept = sleep_data['stop'] - sleep_data['start']

sleep_data['time_slept'] = time_slept

plt.plot(sleep_data['start'], sleep_data['time_slept'])
plt.show()
