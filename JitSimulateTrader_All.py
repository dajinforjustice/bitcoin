import os
from numba import jit
import numpy as np
import h5py
from datetime import datetime, timedelta
from strategy.JitRbreakerStrategy import jit_rbreaker_exit_modified_strategy
from strategy.JitTTMStrategy import jit_ttm_strategy
from strategy.JitRbreakerBullStrategy import jit_rbreaker_bull_strategy
from strategy.volume_breaker.t2 import jit_volume_breaker_strategy
from strategy.break_60_test.break_60 import breaker_60_strategy
from pandas import Series
import plotting
from jit_talib import jit_ma
import pandas as pd
from JitTradeLib import git_order_matching, git_send_order, git_update_chart, git_update_indicator, data_init, create_csv, load_binance_code
import csv

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
        signal = breaker_60_strategy(
            tick_array[tick_index],
            chart,
            position,
            global_data)
        if global_data['executing'] < 1 and abs(signal[0]) > 1e-9:
            git_send_order(
                tick_array[tick_index],
                signal,
                order_all,
                global_data)
            global_data['executing'] = 1
        git_update_chart(tick_array[tick_index], chart, global_data)
        git_update_indicator(tick_array[tick_index], chart, global_data)


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

def all_instrument_test(exchange, contract, date_start, date_end):
    #date_start = datetime(2018, 4, 23)
    #date_end = datetime(2018, 4, 24)
    interval = 1
    exchange = exchange
    trading_pair = contract
    date_start_str = date_start.strftime('%Y-%m-%d')
    date_end_str = date_end.strftime('%Y-%m-%d')
    chart, ret_array, order_all, position, global_data = continuous_backtest(
        date_start, date_end, exchange, trading_pair)
    chart_end = global_data['chart_pos']
    # plotting.plot_ret_and_price(
    #    ret_array.cumsum()[1441:chart_end], chart[1][1441:chart_end])
    open_array, high_array, low_array, close_array, volume_array, dma_array = chart[
                                                                                  1][:], chart[2][:], chart[3][:], \
                                                                              chart[4][:], chart[5][:], chart[7][:]
    dma_array2 = jit_ma(close_array, 10) - jit_ma(close_array, 50)
    dma_smooth_array = jit_ma(dma_array, 10)
    ret_last = ret_array.cumsum()[chart_end]
    if not os.path.exists(os.path.join('./csv', date_start_str + '_' + date_end_str)):
        os.makedirs(os.path.join('./csv', date_start_str + '_' + date_end_str))
    csv_path = os.path.join('./csv', date_start_str + '_' + date_end_str, contract + str(ret_last) + '.csv')
    if abs(ret_last) > 1e-10:
        create_csv(order_all, global_data, csv_path)
    pic_save_path = os.path.join('./csv', date_start_str + '_' + date_end_str, contract + str(ret_last) + '.png')
    plotting.plot_price_indicator_ret(close_array[int(1440 / interval) + 1:chart_end], chart[9][int(
         1440 / interval) + 1:chart_end], ret_array.cumsum()[int(1440 / interval) + 1:chart_end],pic_save_path)
    return ret_last


if __name__ == '__main__':
    path = './txt/binance.code.txt'
    codes = load_binance_code(path)
    ret_dict = {}
    date_start = datetime(2018, 4, 1)
    date_end = datetime(2018, 4, 26)
    date_start_str = date_start.strftime('%Y-%m-%d')
    date_end_str = date_end.strftime('%Y-%m-%d')
    exchange = 'binance'
    ret_total = 0
    backtest_type_str = 'break_60_test_le20'
    for code in codes:
        trading_pair = code.split('/')[1]
        if not trading_pair.endswith('btc'):
            continue
        print(trading_pair)
        #trading_pair = 'btc.usdt'
        ret_last = all_instrument_test(exchange, trading_pair, date_start, date_end)
        ret_dict[code] = ret_last
        print(code, ret_last)
        ret_total+=ret_last
        #break
    with open('./csv/'+ backtest_type_str +'_'+ date_start_str + '_' + date_end_str+'_'+str(ret_total)+ '.csv', 'w') as f:  # Just use 'w' mode in 3.x
        for k,v in ret_dict.items():
            if abs(v)> 1e-10:
                f.write(str(k) + ',' + str(v) + '\n')
        #w = csv.DictWriter(f, ret_dict.keys())
        #w.writeheader()
        #w.writerow(ret_dict)
    try:
        os.rename('./csv/' + date_start_str + '_' + date_end_str,'./csv/'+ backtest_type_str +'_' + date_start_str + '_' + date_end_str + '_' + str(ret_total))
    except:
        print('same result')
    print(ret_total)


