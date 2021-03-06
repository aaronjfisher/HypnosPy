from glob import glob
import pandas as pd
import numpy as np
import os
import warnings

from hypnospy.data import RawProcessing
from hypnospy import Wearable
from hypnospy import Diary


class Experiment(object):

    def __init__(self):
        self.datapath = None
        self.wearables = {}

    def add_wearable(self, w):
        self.wearables[w.get_pid()] = w

    def remove_wearable(self, w):
        if w in self.wearables:
            del self.wearables[w]

    def configure_experiment(self, datapath: str, device_location: str, cols_for_activity, col_for_mets: str = None,
                             is_emno: bool = False, is_act_count: bool = False, col_for_datetime: str = "time",
                             start_of_week: int = -1, strftime: str = None, col_for_pid: str = None, pid: int = -1,
                             additional_data: object = None, col_for_hr: str = None):

        # TODO: Missing a check to see if datapath exists.
        if os.path.isdir(datapath):
            if not datapath.endswith("*"):
                datapath = os.path.join(datapath, "*")
        else:
            if '*' not in datapath:
                datapath = datapath + "*"

        for file in glob(datapath):
            pp = RawProcessing(file,
                               device_location=device_location,
                               # activitiy information
                               cols_for_activity=cols_for_activity,
                               is_act_count=is_act_count,
                               is_emno=is_emno,
                               # Datatime information
                               col_for_datetime=col_for_datetime,
                               col_for_mets=col_for_mets,
                               start_of_week=start_of_week,
                               strftime=strftime,
                               # Participant information
                               col_for_pid=col_for_pid,
                               pid=pid,
                               additional_data=additional_data,
                               # HR information
                               col_for_hr=col_for_hr, )
            w = Wearable(pp)
            self.wearables[w.get_pid()] = w

    def add_diary(self, diary: Diary):
        for pid in diary.data["pid"].unique():
            di = diary.data[diary.data["pid"] == pid]
            w = self.get_wearable(pid)
            if w:
                w.add_diary(Diary().from_dataframe(di))

    def get_wearable(self, pid: str):
        if pid in self.wearables.keys():
            return self.wearables[pid]
        else:
            warnings.warn("Unknown PID %s." % pid)
            return None
            # raise KeyError("Unknown PID %s." % pid)

    def size(self):
        return len(self.wearables)

    def get_all_wearables(self):
        return list(self.wearables.values())

    def set_freq_in_secs(self, freq: int):
        for wearable in self.get_all_wearables():
            wearable.set_frequency_in_secs(freq)

    def change_start_hour_for_experiment_day(self, hour):
        for wearable in self.get_all_wearables():
            wearable.change_start_hour_for_experiment_day(hour)

    def fill_no_activity(self, value):
        for wearable in self.get_all_wearables():
            wearable.fill_no_activity(value)

    def overall_stats(self):
        days_acc = []
        epochs_acc = []
        for wearable in self.get_all_wearables():
            days_acc.append(len(wearable.data[wearable.get_experiment_day_col()].unique()))
            epochs_acc.append(wearable.data.shape[0])

        days_acc = np.array(days_acc)
        epochs_acc = np.array(epochs_acc)
        print("Total number of wearables: %d" % (self.size()))
        print("Total number of days: %d" % days_acc.sum())
        if epochs_acc.size > 0:
            print("Avg. number of days: %.2f (+-%.3f). Max: %d, Min: %d." % (
                days_acc.mean(), days_acc.std(), days_acc.max(), days_acc.min()))
            print("Avg. number of epochs: %.2f (+-%.3f). Max: %d, Min: %d." % (
                epochs_acc.mean(), epochs_acc.std(), epochs_acc.max(), epochs_acc.min()))
        else:
            print("Experiment has no valid wearable left.")

    def create_day_sleep_experiment_day(self, sleep_col: str, new_col: str = 'day_night_sequence',
                                        start_by_awaken_part: bool = True):
        """
        Adds a column to the wearable data.
        This column will be similar to ``experiment_day``, however instead of having a fixed size, it will follow the day/sleep cycle.
        This is not by exploring the annotations made by the SleepBoudaryDetector module, represented here by the ``sleep_col``.

        :param sleep_col: sleep_col resulted from SleepBoudaryDetector.detect_sleep_boundary()
        :param new_col: the name of the new column created
        :param start_by_awaken_part: should we start sequence id 0 with the day part (True) or not (False)
        """

        for wearable in self.get_all_wearables():
            wearable.create_day_sleep_experiment_day(sleep_col, new_col, start_by_awaken_part)

    def weekday(self) -> pd.DataFrame:
        return pd.concat([wearable.weekday() for wearable in self.get_all_wearables()])

    def is_weekend(self, weekend=[5, 6]) -> pd.DataFrame:
        return pd.concat([wearable.is_weekend(weekend) for wearable in self.get_all_wearables()])
