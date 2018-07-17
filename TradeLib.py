import datetime
import pandas as pd
import time
import numpy as np
import arrow


class Bar(object):
    def __init__(self, o, h, l, c, v, a):
        self.open = np.float64(o)
        self.high = np.float64(h)
        self.low = np.float64(l)
        self.close = np.float64(c)
        self.volume = np.float64(v)
        self.amount = np.float64(a)

    def update(self, p, v):
        if p > self.high:
            self.high = p
        if p < self.low:
            self.low = p
        self.close = p
        self.volume += v
        self.amount += v * p


class Chart(object):
    def __init__(self, interval, code, today):
        self.code = code
        self.start_index = -1
        self.now_pos = -1
        self.interval = interval
        self.bars = []
        self.ret_bars = []
        self.last_tick = None
        # 7 days
        continuous_days = 14
        for bar_count in range(1440 * continuous_days):
            bar = Bar(0, 0, 0, 0, 0, 0)
            self.bars.append(bar)
            self.ret_bars.append(0)
        # date_str = datetime.datetime.now().strftime('%Y%m%d%H%M')
        date_str = today.strftime('%Y%m%d')
        today_time_start = time.mktime(time.strptime(date_str, '%Y%m%d'))
        time_interval = (
            np.arange(
                60 * interval,
                24 * 60 * 60 * continuous_days + 60 * interval,
                60 * interval,
                dtype='f8') + today_time_start - 24 * 60 * 60) * 1000
        # pd.timedelta_range()
        self.interval_list = list(time_interval.tolist())

    def update(self, tk):
        self.last_tick = tk
        p, v, t = tk.last, tk.volume, tk.time.timestamp() * 1000
        flag_new = False
        if self.now_pos < 0:
            flag_new = True
            last_price = p
        else:
            last_price = self.bars[self.now_pos].close

        update_index = 0
        while update_index < len(
                self.interval_list) and t > self.interval_list[update_index]:
            update_index += 1
        for replace_index in range(self.now_pos + 1, update_index + 1):
            bar = Bar(last_price, last_price, last_price, last_price, 0, 0)
            self.bars[replace_index] = bar

        if update_index == self.now_pos:
            bar = self.bars[update_index]
            bar.update(p, v)
            self.bars[update_index] = bar
        else:
            bar = Bar(last_price, last_price, last_price, last_price, v, v * p)
            self.bars[update_index] = bar
            self.now_pos = update_index

        if flag_new:
            self.start_index = update_index

    def update_ret(self, ret):
        self.ret_bars[self.now_pos] += ret

    def to_ohlc_array(self):
        s_index = self.start_index
        #s_index = 0
        e_index = self.now_pos
        open_list = [bar.open for bar in self.bars[s_index:e_index + 1]]
        high_list = [bar.high for bar in self.bars[s_index:e_index + 1]]
        low_list = [bar.low for bar in self.bars[s_index:e_index + 1]]
        close_list = [bar.close for bar in self.bars[s_index:e_index + 1]]
        ohlc_array = [
            np.array(
                open_list, dtype='f8'), np.array(
                high_list, dtype='f8'), np.array(
                low_list, dtype='f8'), np.array(
                    close_list, dtype='f8')]
        return ohlc_array


class Signal(object):
    def __init__(self, code, open_close, direction, volume, price):
        self.code = code
        self.open_close = open_close
        self.direction = direction
        self.volume = volume
        self.price = price


    def __str__(self):
        return '<{} {} {} {} {}>'.format(
            self.code,
            self.open_close,
            self.direction,
            self.volume,
            self.price)


class Position(object):
    def __init__(
            self,
            code,
            volume,
            avg_price,
            entry_price,
            entry_time,
            direction):
        self.code = code
        self.volume = volume
        self.avg_price = avg_price
        self.entry_price = entry_price
        self.entry_time = entry_time
        self.direction = direction

    def __str__(self):
        return '<{} {} {} {} {}>'.format(
            self.code,
            self.avg_price,
            self.direction,
            self.volume,
            self.entry_price)
