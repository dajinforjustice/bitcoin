import os
from numba import jit
import numpy as np
import h5py
from datetime import datetime, timedelta
from strategy.JitRbreakerStrategy import jit_rbreaker_exit_modified_strategy
from pandas import Series
import plotting
from jit_talib import jit_ma
import pandas as pd
from JitTradeLib import git_order_matching, git_send_order, git_update_chart, git_update_indicator, data_init, create_csv

def backtest(tick_array_1,tick_array_2):
    pass

def continuous_backtest(date_start, date_end, exchange, trading_pair1, trading_pair2):
    while date_start < date_end:
        date_start_str = date_start.strftime('%Y-%m-%d')
        h5_path_1 = os.path.join(
            './data_h5/',
            exchange,
            trading_pair1,
            date_start_str,
            date_start_str +
            '.h5')
        h5_path_2 = os.path.join(
            './data_h5/',
            exchange,
            trading_pair2,
            date_start_str,
            date_start_str +
            '.h5')
        try:
            h5_file_1 = h5py.File(h5_path_1, 'r')
            tick_length_1 = h5_file_1['tick_array'].attrs['length']
            tick_array_1 = h5_file_1['tick_array'][:]
            h5_file_1.close()
            h5_file_2 = h5py.File(h5_path_2, 'r')
            tick_length_2 = h5_file_2['tick_array'].attrs['length']
            tick_array_2 = h5_file_2['tick_array'][:]
            h5_file_2.close()
        except BaseException:
            date_start += timedelta(days=1)
            continue
        backtest(tick_array_1,tick_array_2)
        # final_path = os.path.join(
        #     './data_h5/',
        #     exchange,
        #     trading_pair,
        #     'final.h5')
        # file_final_h5 = h5py.File(final_path, 'r')
        # tick_array = file_final_h5['final_array'][:]
        # tick_length = len(tick_array)

        print(date_start_str, 'done')
        # break
        date_start += timedelta(days=1)
    print('done')