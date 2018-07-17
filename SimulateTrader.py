import pandas as pd
import os
from TradeLib import Signal, Position, Chart
from onetoken.model import Tick
from datetime import datetime
from Strategy import strategy_1
import json
import arrow
import numpy as np
from pandas import Series


class SimulateTrader(object):
    def __init__(self, symbol):
        self.chart_dict = {}
        self.position_dict = {}
        self.trading_status = {}
        self.symbol = symbol
        self.pending_signals = []

    def update_chart(self, line):
        data = json.loads(line)
        data['price'] = data['last']
        s = arrow.get(data['time'])
        # print(data['time'])
        data['time'] = s
        contract = data['contract']
        tk = Tick.init_with_dict(data)
        self.chart_dict[contract].update(tk)

    def add_data(self, data):
        self.new_data = data

    # version: order price matching
    def order_matching(self, line):
        rest_signals = []
        data = json.loads(line)
        data['price'] = data['last']
        s = arrow.get(data['time'])
        # data['time'] = s
        contract = data['contract']
        for signal in self.pending_signals:
            if signal.code == contract:
                if signal.open_close == 'open':
                    pos = Position(
                        contract,
                        signal.volume,
                        signal.price,
                        signal.price,
                        data['time'],
                        'b' if signal.direction == 1 else 's')
                    self.position_dict[contract] = pos
                else:
                    pos = self.position_dict[contract]
                    direction = 1 if pos.direction == 'b' else -1
                    ret = np.float((signal.price - pos.avg_price)) * \
                        direction * np.float(pos.volume)
                    self.chart_dict[contract].update_ret(ret)
                    self.position_dict[contract] = None
                    self.trading_status[contract] = None
            self.trading_status[contract] = None
        self.pending_signals = rest_signals

    def send_order(self, signal: Signal):
        self.pending_signals.append(signal)

    def add_contract(self, contract, interval):
        data_first = json.loads(self.new_data[0])
        s = arrow.get(data_first['time'])
        if contract not in self.chart_dict:
            self.chart_dict[contract] = Chart(interval, contract, s)
        if contract not in self.trading_status:
            self.trading_status[contract] = None

    def run(self):
        # todo
        self.add_contract(self.symbol, 1)
        i = 0
        for line in self.new_data:
            self.order_matching(line)
            signals = set()
            for code, chart in self.chart_dict.items():
                if code in self.position_dict:
                    pos = self.position_dict[code]
                else:
                    pos = None
                signal = strategy_1(self.chart_dict[code], pos)
                if signal:
                    signals.add(signal)

            for signal in signals:
                if not self.trading_status[signal.code]:
                    self.trading_status[signal.code] = 'executing'
                    self.send_order(signal)
            self.update_chart(line)
            i += 1
            if i % 500 == 0:
                print(i)
            if i % 20000 == 0:
                break  # print(i,'done')


exchange = 'binance'
date_start = datetime(2018, 3, 20)
date_end = datetime(2018, 3, 21)
date_start_str = date_start.strftime('%Y-%m-%d')
trading_symbol = 'btc.usdt:xtc.binance'
trading_pair = trading_symbol.split(':')[0]
json_path = os.path.join(
    './data_json/',
    exchange,
    trading_pair,
    date_start_str,
    date_start_str +
    '.json')
f = open(json_path, 'r')
s_trader = SimulateTrader(trading_symbol)
data = f.readlines()
s_trader.add_data(data)
s_trader.run()
open_price_array = np.array(
    [t.open for t in s_trader.chart_dict[trading_symbol].bars])
Series(open_price_array[:]).plot()
ret_array = np.array(s_trader.chart_dict[trading_symbol].ret_bars)
#data =pd.read_json(json_path,orient='records',lines='True')
