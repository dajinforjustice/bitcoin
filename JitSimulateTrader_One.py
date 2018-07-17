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


@jit(nopython=True)
def backtest(
        tick_array,
        tick_length,
        chart,
        ret_array,
        order_all,
        position,
        global_data):
    print(tick_length)
    for tick_index in range(tick_length):
        git_order_matching(
            chart,
            ret_array,
            tick_array[tick_index],
            order_all,
            position,
            global_data)
        signal = jit_rbreaker_exit_modified_strategy(
            tick_array[tick_index],
            chart,
            position,
            global_data)
        if global_data['executing'] < 1 and abs(signal[0]) > 1e-9:
            # print(signal)
            git_send_order(
                tick_array[tick_index],
                signal,
                order_all,
                global_data)
            # print(tick_index)
            global_data['executing'] = 1
        git_update_chart(tick_array[tick_index], chart, global_data)
        git_update_indicator(tick_array[tick_index], chart, global_data)
        # if tick_index % 5000 == 0:
        #    print((tick_index + 1) / tick_length * 100)
        #    print(tick_index, '/', tick_length, '%.2f%%' %
        #          ((tick_index + 1) / tick_length * 100))


def continuous_backtest(date_start, date_end, exchange, trading_pair):
    chart, ret_array, order_all, position, global_data = data_init(date_start)
    while date_start < date_end:
        date_start_str = date_start.strftime('%Y-%m-%d')
        h5_path = os.path.join(
            './data_h5/',
            exchange,
            trading_pair,
            date_start_str,
            date_start_str +
            '.h5')
        try:
            h5_file = h5py.File(h5_path, 'r')
            tick_length = h5_file['tick_array'].attrs['length']
            tick_array = h5_file['tick_array'][:]
            h5_file.close()
        except BaseException:
            date_start += timedelta(days=1)
            continue

        # final_path = os.path.join(
        #     './data_h5/',
        #     exchange,
        #     trading_pair,
        #     'final.h5')
        # file_final_h5 = h5py.File(final_path, 'r')
        # tick_array = file_final_h5['final_array'][:]
        # tick_length = len(tick_array)
        backtest(
            tick_array,
            tick_length,
            chart,
            ret_array,
            order_all,
            position,
            global_data)
        print(date_start_str, 'done')
        # break
        date_start += timedelta(days=1)
    print('done')
    return chart, ret_array, order_all, position, global_data


date_start = datetime(2018, 2, 1)
date_end = datetime(2018, 5, 9)
exchange = 'binance'
trading_pair = 'btc.usdt'
date_start_str = date_start.strftime('%Y-%m-%d')
chart, ret_array, order_all, position, global_data = continuous_backtest(
    date_start, date_end, exchange, trading_pair)
chart_end = global_data['chart_pos']
# plotting.plot_ret_and_price(
#    ret_array.cumsum()[1441:chart_end], chart[1][1441:chart_end])
open_array, high_array, low_array, close_array, volume_array, dma_array = chart[
    1][:], chart[2][:], chart[3][:], chart[4][:], chart[5][:], chart[7][:]
dma_array2 = jit_ma(close_array, 10) - jit_ma(close_array, 50)
dma_smooth_array = jit_ma(dma_array, 10)
csv_path = 'test.csv'
create_csv(order_all, global_data, csv_path)

plotting.plot_price_indicator_ret(
    close_array[1441:chart_end], chart[9][1441:chart_end], ret_array.cumsum()[1441:chart_end],'')
