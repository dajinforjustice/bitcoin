import os
import pandas as pd
import json
from TradeLib import Chart
from datetime import datetime, timedelta
from onetoken.model import Tick
import numpy as np
import arrow
import pickle
import h5py
from download_data import uncompress_file
from JitTradeLib import load_binance_code

def json_2_min_bitcoin(code, json_path, pkl_path, today):
    if os.path.exists(os.path.join('./data/pkl/', code, pkl_path + '.pkl')):
        f = open(os.path.join('./data/pkl/', code, pkl_path + '.pkl'), 'rb')
        print('loaded from pkl file')
        return pickle.load(f)
    chart = Chart(1, code, today)
    t = 0
    for line in open(json_path, 'r'):
        data = json.loads(line)
        data['price'] = data['last']
        s = arrow.get(data['time'])
        data['time'] = s
        tk = Tick.init_with_dict(data)
        chart.update(tk)
        t += 1
    print(json_path, 'done')
    if not os.path.exists(os.path.join('./data/pkl/', code)):
        os.makedirs(os.path.join('./data/pkl/', code))
    pickle.dump(
        chart.to_ohlc_array(),
        open(
            os.path.join(
                './data/pkl/',
                code,
                pkl_path +
                '.pkl'),
            'wb'))
    return chart.to_ohlc_array()

def json_2_h5(code, json_path, h5_path):
    json_file = open(json_path, 'r')
    lines = json_file.readlines()
    file_h5 = h5py.File(h5_path, 'w')
    tick_array = np.zeros((len(lines), 1 + 40 + 40 + 3), dtype='f8')
    for index, line in enumerate(lines):
        data = json.loads(line)
        time = arrow.get(data['time'])
        tick_array[index][0] = time.float_timestamp
        for i, asks in enumerate(data['asks']):
            tick_array[index][i + 1] = asks['price']
            tick_array[index][i + 21] = asks['volume']
        for i, bids in enumerate(data['bids']):
            tick_array[index][i + 41] = bids['price']
            tick_array[index][i + 61] = bids['volume']
        tick_array[index][81] = data['last']
        tick_array[index][82] = data['volume']
        try:
            tick_array[index][83] = data['amount']
        except BaseException:
            pass
    data_tick = file_h5.create_dataset(
        'tick_array', data=tick_array, compression="gzip")
    data_tick.attrs['length'] = len(lines)
    file_h5.close()
    print(h5_path, 'done')

def json_2_h5_range(exchange, trading_pair, date_start, date_end):
    while date_start < date_end:
        try:
            date_start_str = date_start.strftime('%Y-%m-%d')
            json_path = os.path.join(
                './data_json/',
                exchange,
                trading_pair,
                date_start_str,
                date_start_str +
                '.json')
            if not os.path.exists(
                os.path.join(
                    './data_h5/',
                    exchange,
                    trading_pair,
                    date_start_str)):
                os.makedirs(
                    os.path.join(
                        './data_h5/',
                        exchange,
                        trading_pair,
                        date_start_str))
            h5_path = os.path.join(
                './data_h5/',
                exchange,
                trading_pair,
                date_start_str,
                date_start_str + '.h5')
            if 1:
                fn_in = json_path[:-5]+'.gz'
                if not os.path.exists(json_path):
                    uncompress_file(fn_in,json_path)
                json_2_h5(trading_pair, json_path, h5_path)
                os.remove(json_path)

        except Exception as e:
            print(e)
        date_start += timedelta(days=1)


def h5_merge():
    date_start = datetime(2018, 2, 1)
    date_end = datetime(2018, 4, 9)
    trading_pair = 'btc.usdt'
    exchange = 'binance'
    first = True
    final_array = None
    while date_start < date_end:
        try:
            date_start_str = date_start.strftime('%Y-%m-%d')
            h5_path = os.path.join(
                './data_h5/',
                exchange,
                trading_pair,
                date_start_str,
                date_start_str + '.h5')
            h5_file = h5py.File(h5_path, 'r')
            tick_length = h5_file['tick_array'].attrs['length']
            tick_array = h5_file['tick_array'][:]
            if first:
                final_array = tick_array
                first = False
            else:
                final_array = np.concatenate((final_array,tick_array))
            print(date_start_str, 'done')

        except Exception as e:
            print(e)

        date_start += timedelta(days=1)
    final_path = os.path.join(
                './data_h5/',
                exchange,
                trading_pair,
                'final.h5')
    file_final_h5 = h5py.File(final_path, 'w')
    data_tick = file_final_h5.create_dataset(
        'final_array', data=final_array, compression="gzip")
    data_tick.attrs['length'] = len(final_array)
    file_final_h5.close()

if __name__ == '__main__':
    #h5_merge()
    path = './txt/binance.code.txt'
    codes = load_binance_code(path)
    date_start = datetime(2018, 5, 1)
    date_end = datetime(2018, 5, 20)
    exchange = 'binance'
    flag = 1
    for code in codes:
        trading_pair = code.split('/')[1]
        trading_pair = 'btc.usdt'
        print(trading_pair)
        if trading_pair == 'trx.btc':
            flag = 1
        if flag:
            json_2_h5_range(exchange, trading_pair, date_start, date_end)
        break


