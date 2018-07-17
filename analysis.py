import importlib
import data_engine
import os
from datetime import datetime, timedelta
from TradeLib import Position, Signal, Chart
import numpy as np
import Strategy
import plotting
from pandas import Series
import matplotlib.pyplot as plt
import talib

def multi_days():
    importlib.reload(data_engine)
    importlib.reload(Strategy)
    date_start = datetime(2018, 4, 1)
    date_end = datetime(2018, 4, 2)
    ret_sum_list = []
    day_close_list = []
    trading_pair = 'bnb.usdt'
    exchange = 'binance'
    while date_start < date_end:
        try:
            date_start_str = date_start.strftime('%Y-%m-%d')
            [o, h, l, c] = data_engine.json_2_min_bitcoin(trading_pair,
                                                          os.path.join('./data_json/', exchange, trading_pair,
                                                                       date_start_str, date_start_str + '.json'),
                                                          date_start_str, date_start)
            print(date_start_str)
            [para1, para2, para3, para4, para5] = [0.3, 0.7, 0.9, 90, 90]
            if o[0] < 1:
                pass
            o_r = []
            h_r = []
            l_r = []
            c_r = []
            length = len(o)
            for i in range(length):
                if o[i] > 0 and h[i] > 0 and l[i] > 0 and c[i] > 0:
                    o_r.append(o[i])
                    h_r.append(h[i])
                    l_r.append(l[i])
                    c_r.append(c[i])
            ret_array = Strategy.strategy_1_backtest(o_r, h_r, l_r, c_r, para1, para2, para3, para4, para5)
            ret_sum_list.append(ret_array.cumsum()[-1])
            day_close_list.append(o[0])
            plotting.plot_ret_and_price(ret_array.cumsum(), c_r)
            print(date_start_str, ret_array.cumsum()[-1])

        except Exception as e:
            print(e)

        date_start += timedelta(days=1)
    ret_sum_array = np.array(ret_sum_list)
    day_close_array = np.array(day_close_list)
    #plotting.plot_ret_and_price(ret_sum_array.cumsum(), day_close_array)

def continuous_days():
    importlib.reload(data_engine)
    importlib.reload(Strategy)
    date_start = datetime(2018, 2, 15)
    date_end = datetime(2018, 2, 20)
    trading_pair = 'btc.usdt'
    exchange = 'binance'
    date_start_str = date_start.strftime('%Y-%m-%d')
    [o_array, h_array, l_array, c_array] = data_engine.json_2_min_bitcoin(trading_pair,
                                                  os.path.join('./data_json/', exchange, trading_pair,
                                                               date_start_str, date_start_str + '.json'),
                                                  date_start_str, date_start)
    while date_start < date_end:
        try:
            date_start_str = date_start.strftime('%Y-%m-%d')
            [o, h, l, c] = data_engine.json_2_min_bitcoin(trading_pair,
                                                          os.path.join('./data_json/', exchange, trading_pair,
                                                                       date_start_str, date_start_str + '.json'),
                                                          date_start_str, date_start)

            o_r = []
            h_r = []
            l_r = []
            c_r = []
            length = len(o)
            for i in range(length):
                if o[i] > 0 and h[i] > 0 and l[i] > 0 and c[i] > 0:
                    o_r.append(o[i])
                    h_r.append(h[i])
                    l_r.append(l[i])
                    c_r.append(c[i])


            o_array = np.append(o_array, np.array(o_r))
            h_array = np.append(h_array, np.array(h_r))
            l_array = np.append(l_array, np.array(l_r))
            c_array = np.append(c_array, np.array(c_r))

            #ret_array = Strategy.strategy_2_backtest(o, h, l, c, para1, para2, para3)
            #ret_sum_list.append(ret_array.cumsum()[-1])
            #day_close_list.append(o[0])
            #plotting.plot_ret_and_price(ret_array.cumsum(), c)
            #print(date_start_str, ret_array.cumsum()[-1])

        except Exception as e:
            print(e)
        print(date_start)
        date_start += timedelta(days=1)

    [para1, para2, para3, para4, para5] = [0.3, 0.7, 0.9, 90, 90]

    ret_array = Strategy.strategy_ttm_squeeze_backtest(o_array, h_array, l_array, c_array, para1, para2, para3)
    #ret_array = Strategy.strategy_1_backtest(o_array, h_array, l_array, c_array, para1, para2, para3, para4, para5)
    #ret_array = Strategy.strategy_1_1_backtest(o_array, h_array, l_array, c_array, para1, para2, para3, para4, para5)
    plotting.plot_ret_and_price(ret_array.cumsum(), c_array)
    #ret_sum_array = np.array(ret_sum_list)
    #day_close_array = np.array(day_close_list)
    #plotting.plot_ret_and_price(ret_sum_array.cumsum(), day_close_array)

if __name__ == '__main__':
    continuous_days()
    #multi_days()