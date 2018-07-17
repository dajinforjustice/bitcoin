import numpy as np
from datetime import datetime
import time
import pandas as pd


def data_init(date_start):
    record_count = 100000
    continuous_days = 90
    interval = 1
    chart = np.zeros((9, 1440 * continuous_days), dtype='f8')
    # time,o,h,l,c,v,a,indicator1,indicator2
    ret_array = np.zeros((1440 * continuous_days), dtype='f8')
    # time_interval, o,h,l,c,v,amount
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


def create_csv(order_all, global_data, csv_path):
    final_order = order_all[:global_data['order_quantity']]
    final_df = pd.DataFrame(final_order)
    final_df['position_index'] = final_df['entrust_time'].apply(
        lambda x: datetime.fromtimestamp(x).hour * 60 + datetime.fromtimestamp(x).minute)
    final_df['entrust_time'] = final_df['entrust_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    final_df['cancel_time'] = final_df['cancel_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    final_df['finish_time'] = final_df['finish_time'].apply(
        lambda x: datetime.fromtimestamp(x).strftime('%H:%M:%S'))
    final_df['type'] = final_df['type'].apply(
        lambda x: 'open' if x == 1 else 'close')
    final_df['bs'] = final_df['bs'].apply(
        lambda x: 'buy' if x == 1 else 'sell')
    final_df.to_csv(csv_path)
