from numba import jit
import numpy as np
import time
import arrow
from onetoken.model import Tick
from jit_talib import jit_ma
from api.client import Client
import pandas as pd
from datetime import datetime
import onetoken as ot
class JitInstrument(object):
    def __init__(self, contract, date_start):
        self.code = contract
        chart, ret_array, order_all, position, global_data = data_init(date_start)
        self.chart = chart
        self.position = position
        self.global_data = global_data
        self.last_tick = np.zeros((1 + 40 + 40 + 3), dtype='f8')
        self.is_delay = True

    def update(self, tk: Tick):
        jit_tick = np.zeros((1 + 40 + 40 + 3), dtype='f8')
        data = tk.to_dict()
        time = arrow.get(data['time'])
        jit_tick[0] = time.float_timestamp
        for i, asks in enumerate(data['asks']):
            jit_tick[i + 1] = asks['price']
            jit_tick[i + 21] = asks['volume']
        for i, bids in enumerate(data['bids']):
            jit_tick[i + 41] = bids['price']
            jit_tick[i + 61] = bids['volume']
        jit_tick[81] = data['price']
        jit_tick[82] = data['volume']
        self.last_tick = jit_tick
        git_update_chart(jit_tick, self.chart, self.global_data)
        git_update_indicator(jit_tick, self.chart, self.global_data)

class JitSignal(object):
    def __init__(self, code, signal):
        self.code = code
        self.open_close = 'open' if signal[0] > 0 else 'close'
        self.direction = signal[1]
        self.volume = signal[2]
        self.price = signal[3]


    def __str__(self):
        return '<{} {} {} {} {}>'.format(
            self.code,
            self.open_close,
            self.direction,
            self.volume,
            self.price)

@jit(nopython=True)
def git_order_matching(
        chart,
        ret_array,
        tick,
        order_all,
        position,
        global_data):
    order_quantity = global_data['order_quantity']
    for index in range(order_quantity):
        if order_all['status'][index] > 0:
            if (order_all['entrust_price'][index] - tick[81]) * \
                    order_all['bs'][index] >= 0:
                order_all['dealt_amount'][index] += min(tick[82],order_all['entrust_volume'][index] - order_all['dealt_volume'][index]) * tick[81]
                #(order_all['entrust_volume'][index] - order_all['dealt_volume'][index]) * tick[81]
                order_all['dealt_volume'][index] += min(tick[82],order_all['entrust_volume'][index] -order_all['dealt_volume'][index])
                    #min(tick[82],order_all['entrust_volume'][index] -order_all['dealt_volume'][index])
                    #order_all['entrust_volume'][index] - order_all['dealt_volume'][index]

                if order_all['dealt_volume'][index] > 0:
                    order_all['avg_dealt_price'][index] = order_all['dealt_amount'][index] / \
                        order_all['dealt_volume'][index]

            if order_all['entrust_volume'][index] - \
                    order_all['dealt_volume'][index] < 1e-9:
                order_all['status'][index] = 0
                global_data['executing'] = 0
                order_all['finish_time'][index] = tick[0]
                if order_all['type'][index] == 1:  # open_order
                    position['volume'] = order_all['dealt_volume'][index]
                    position['avg_price'] = order_all['avg_dealt_price'][index]
                    position['entry_time'] = tick[0]
                    position['direction'] = order_all['bs'][index]
                    position['status'] = 1
                    #global_data['position_index'] += 1
                else:  # close_order
                    # print(position['avg_price'])
                    # print(order_all['avg_dealt_price'][index])
                    # print(order_all['entrust_volume'][index])

                    # order_all['commission_rate'][index]\

                    ret_array[global_data['chart_pos']] += position['direction'] * position['volume'] * (
                        order_all['avg_dealt_price'][index] - position['avg_price']) - \
                        order_all['commission_rate'][index] * (
                        order_all['avg_dealt_price'][index] +
                        position['avg_price']) * position[
                        'volume']
                    position['status'] = 0
                    position['volume'] = 0
                    position['avg_price'] = 0
                    position['entry_time'] = 0
                    position['direction'] = 0

            elif tick[0] > order_all['cancel_time'][index]:
                order_all['finish_time'][index] = tick[0]
                if order_all['type'][index] == 1:  # open_order
                    order_all['status'][index] = 0
                    if order_all['dealt_volume'][index] > 1e-9:
                        position['volume'] = order_all['dealt_volume'][index]
                        position['avg_price'] = order_all['avg_dealt_price'][index]
                        position['entry_time'] = tick[0]
                        position['direction'] = order_all['bs'][index]
                        position['status'] = 1
                    global_data['executing'] = 0
                    #global_data['position_index'] += 1
                else:
                    order_all['status'][index] = 0
                    t = global_data['order_quantity']
                    order_all['entrust_time'][t] = tick[0]
                    order_all['bs'][t] = order_all['bs'][index]
                    order_all['entrust_volume'][t] = order_all['entrust_volume'][index] - \
                        order_all['dealt_volume'][index]
                    order_all['entrust_price'][t] = tick[1] if order_all['bs'][index] > 0 else tick[41]
                    # print(order_all['entrust_price'][t])
                    # print(order_all['entrust_volume'][t])
                    order_all['commission_rate'][t] = order_all['commission_rate'][index]
                    order_all['status'][t] = 1
                    order_all['type'][t] = -1
                    order_all['cancel_time'][t] = order_all['entrust_time'][index] + 30
                    global_data['order_quantity'] += 1
    # return 0


@jit(nopython=True)
def git_send_order(tick, signal, order_all, global_data):
    order_quantity = global_data['order_quantity']
    #order_quantity += 1
    # print(signal)
    order_all['type'][order_quantity] = signal[0]
    order_all['entrust_price'][order_quantity] = signal[3]
    order_all['entrust_time'][order_quantity] = tick[0]
    order_all['entrust_volume'][order_quantity] = signal[2]
    order_all['bs'][order_quantity] = signal[1]
    order_all['cancel_time'][order_quantity] = order_all['entrust_time'][order_quantity] + 10
    order_all['commission_rate'][order_quantity] = 0.0005
    order_all['status'][order_quantity] = 1
    global_data['order_quantity'] += 1


@jit(nopython=True)
def git_update_indicator(tick, chart, global_data):
    now_pos = global_data['chart_pos']
    close_array = chart[4][:]
    ma_10_last = jit_ma(close_array[now_pos - 9:now_pos + 1], 10)[-1]
    ma_50_last = jit_ma(close_array[now_pos - 49:now_pos + 1], 50)[-1]
    ma_20_last = jit_ma(close_array[now_pos - 19:now_pos + 1], 20)[-1]
    dma_last = ma_10_last - ma_50_last
    chart[7][now_pos] = dma_last
    tr = max(abs(chart[2][now_pos] - chart[3][now_pos]), abs(chart[4][now_pos - 1] - chart[2][now_pos]),
             abs(chart[4][now_pos - 1] - chart[3][now_pos]))
    chart[8][now_pos] = tr
    chart[9][now_pos] = jit_ma(chart[8][now_pos - 9: now_pos + 1], 10)[-1]
    chart[10][now_pos] = ma_20_last

@jit(nopython=True)
def git_update_chart(tick, chart, global_data):
    now_pos = global_data['chart_pos']
    p, v, t = tick[81], tick[82], tick[0]
    if now_pos < 0:
        last_price = p
    else:
        last_price = chart[4][now_pos]

    update_index = 0
    while update_index < len(chart[4]) and t > chart[0][update_index]:
        update_index += 1
    for replace_index in range(now_pos + 1, update_index + 1):
        chart[1][replace_index] = last_price
        chart[2][replace_index] = last_price
        chart[3][replace_index] = last_price
        chart[4][replace_index] = last_price

    if update_index == now_pos:
        if p > chart[2][update_index]:
            chart[2][update_index] = p
        if p < chart[3][update_index]:
            chart[3][update_index] = p
        chart[4][update_index] = p
        chart[5][update_index] += v
        chart[6][update_index] += v * p

    else:
        chart[1][update_index] = p
        chart[2][update_index] = p
        chart[3][update_index] = p
        chart[4][update_index] = p
        chart[5][update_index] = v
        chart[6][update_index] = v * p
        global_data['chart_pos'] = update_index


def data_init(date_start):
    record_count = 100000
    continuous_days = 180
    interval = 1
    chart = np.zeros((11, int(1440 / interval * continuous_days)), dtype='f8')
    # time,o,h,l,c,v,a,dma,atr
    ret_array = np.zeros(int((1440 / (interval) * continuous_days)), dtype='f8')
    # time_interval, o,h,l,c,v,amount
    #start_datetime = datetime.fromtimestamp(start_timestamp)
    #date_str = start_datetime.strftime('%Y%m%d')
    date_str = date_start.strftime('%Y-%m-%d')
    today_time_start = time.mktime(time.strptime(date_str, '%Y-%m-%d'))
    time_interval = (
        np.arange(
            60 *
            interval,
            24 *
            60 *
            60 *
            continuous_days +
            60 *
            interval,
            60 *
            interval,
            dtype='f8') +
        today_time_start -
        24 *
        60 *
        60)
    chart[0][:] = time_interval

    order_all_type = np.dtype([('entrust_time', 'f8'),  # type: #timestamp
                               ('bs', 'i4'),  # 1: buy, -1: sell
                               ('entrust_volume', 'f8'),
                               ('entrust_price', 'f8'),
                               ('dealt_volume', 'f8'),
                               ('dealt_amount', 'f8'),
                               ('avg_dealt_price', 'f8'),
                               ('commission_rate', 'f8'),
                               ('status', 'i4'),  # 0:done, 1:matching
                               ('type', 'i4'),  # 1 open_order, -1: close_order
                               # time > cancel_time ->cancel type:timestamp
                               ('finish_time', 'f8'),
                               ('cancel_time', 'f8'),
                               ('position_index', 'i4'),
                               ])

    order_all = np.zeros(2 * record_count, dtype=order_all_type)

    position_type = np.dtype([('volume', 'f8'),
                              ('avg_price', 'f8'),
                              ('entry_time', 'f8'),
                              ('direction', 'i4'),  # 1: long, -1:short
                              ('status', 'i4'),  # 0: done, 1: holding
                              ])

    position = np.zeros(1, dtype=position_type)[0]

    global_data_type = np.dtype(
        [('position_index', 'i4'), ('order_quantity', 'i4'), ('chart_pos', 'i4'), ('executing', 'i4')])

    global_data = np.zeros(1, dtype=global_data_type)[0]
    global_data['chart_pos'] = -1

    return chart, ret_array, order_all, position, global_data


def jit_load_kline(instrument: JitInstrument):
    client = Client('', '')
    code = ''.join(instrument.code.split('/')[-1].split('.')).upper()
    fetched_data = client.get_klines(symbol=code, interval='1m', limit = 100)
    print('kline fetched')

    k = 0
    for data in fetched_data:
        start_time = data[0] / 1000.0
        end_time = data[6] / 1000.0
        # print(datetime.datetime.fromtimestamp(start_time/1000.0).strftime('%Y %m %d %H %M %S'))
        print(k)
        k+=1
        for index in range(len(instrument.chart[0]) - 1):
            # print(datetime.datetime.fromtimestamp(chart.interval_list[index] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(chart.interval_list[index+1] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(start_time / 1000.0).strftime('%Y%m%d %H%M%S'))
            if start_time >= instrument.chart[0][index] and end_time <= instrument.chart[0][index + 1]:
                # print(chart.interval_list[index], start_time, end_time)
                instrument.chart[1][index] = data[1]
                instrument.chart[2][index] = data[2]
                instrument.chart[3][index] = data[3]
                instrument.chart[4][index] = data[4]
                instrument.chart[5][index] = data[5]
                instrument.global_data['chart_pos'] = index
    print(code, ' load done')


async def jit_load_kline_from_1token(instrument: JitInstrument):
    #client = Client('', '')
    code = ''.join(instrument.code.split('/')[-1].split('.')).upper()
    #fetched_data = client.get_klines(symbol=code, interval='1m', limit = 100)
    since = arrow.now().float_timestamp - 60 * 60
    candles, err = await ot.quote.get_candles(instrument.code, '1m', since)

    #print(data, err)
    print('kline fetched')

    k = 0
    for candle in candles:
        start_time = arrow.get(candle['time']).float_timestamp
        #end_time = data[6] / 1000.0
        # print(datetime.datetime.fromtimestamp(start_time/1000.0).strftime('%Y %m %d %H %M %S'))
        print(k)
        k+=1
        for index in range(len(instrument.chart[0]) - 1):
            # print(datetime.datetime.fromtimestamp(chart.interval_list[index] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(chart.interval_list[index+1] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(start_time / 1000.0).strftime('%Y%m%d %H%M%S'))
            if start_time >= instrument.chart[0][index] and start_time < instrument.chart[0][index + 1]:
                # print(chart.interval_list[index], start_time, end_time)
                instrument.chart[1][index] = candle['open']
                instrument.chart[2][index] = candle['high']
                instrument.chart[3][index] = candle['low']
                instrument.chart[4][index] = candle['close']
                instrument.chart[5][index] = candle['volume']
                instrument.global_data['chart_pos'] = index
                break
    print(code, ' load done')

def load_binance_code(path):
    ret_list = []
    f = open(path, 'r')
    code_names = f.readlines()
    for code_name in code_names:
        base = code_name.replace("\n", "").split('.')[1]
        if base != 'ETH' and base!='USDT':
            ret_list.append('binance/' + code_name.lower().replace("\n", ""))
    return ret_list

def create_csv(order_all, global_data, csv_path):
    final_order = order_all[:global_data['order_quantity']]
    final_df = pd.DataFrame(final_order)
    final_df['position_index'] = final_df['entrust_time'].apply(
        lambda x: datetime.fromtimestamp(x).hour * 60 + datetime.fromtimestamp(x).minute)
    final_df['entrust_time'] = final_df['entrust_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    final_df['cancel_time'] = final_df['cancel_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    try:
        final_df['finish_time'] = final_df['finish_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    except:
        print('last not done')

    final_df['type'] = final_df['type'].apply(
        lambda x: 'open' if x == 1 else 'close')
    final_df['bs'] = final_df['bs'].apply(
        lambda x: 'buy' if x == 1 else 'sell')
    final_df.to_csv(csv_path)
