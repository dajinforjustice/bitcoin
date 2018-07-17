from numba import jit
from jit_talib import jit_ma
import numpy as np
from datetime import datetime

@jit(nopython=True)
def jit_ttm_strategy(tick, chart, position, global_data):
    now_pos = global_data['chart_pos']
    open_volume = 0.05
    open_array, high_array, low_array, close_array = chart[1][:
                                                              ], chart[2][:], chart[3][:], chart[4][:]
    ret_signal = np.zeros((4))
    #signal = None
    hp = -9999
    pos = position
    if tick[0] < 1e-5:
        return ret_signal
    if pos['status'] > 0:  # holding
        direction = pos['direction']
        op = pos['avg_price']
        index = now_pos
        hp = direction * (close_array[index] - op)
        [para1, para2, para3, para4, para5, atr_stop_gain] = [0.2, 0.55, 0.33, 90, 90, 3]
        para30 = 30
        if 0:
            print(datetime.now().strftime('%H:%M:%S'), ' hp / op %.5f' % (hp / op), 'open_price:', op, 'last:',
                  close_array[index])
        if now_pos < 1440 + para30:
            return ret_signal
        open_distance = int((tick[0] - pos['entry_time']) / 60)
        peak_price = np.max(high_array[now_pos - open_distance: now_pos + 1]) if direction > 0 else np.min(
           high_array[now_pos - open_distance: now_pos + 1])

        last_30_index = int(now_pos / para30) * para30
        min_30_high = np.max(high_array[last_30_index - para30:last_30_index])
        min_30_low = np.min(low_array[last_30_index - para30:last_30_index])
        min_30_close = close_array[last_30_index - 1]
        Ssetup = min_30_high + para1 * (min_30_close - min_30_low)
        Bsetup = min_30_low - para1 * (min_30_high - min_30_close)
        Senter = (1 + para3) / 2 * (min_30_high +
                                    min_30_low) - para3 * min_30_low
        Benter = (1 + para3) / 2 * (min_30_high +
                                    min_30_low) - para3 * min_30_high
        Sbreak = Bsetup - para2 * (Ssetup - Bsetup)
        Bbreak = Ssetup + para2 * (Ssetup - Bsetup)


        #long stop gain
        if direction > 0 and close_array[now_pos] > op + direction * chart[9][now_pos-1] * atr_stop_gain:# and hp/op > 0.01:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
                                                                             1, (-1) * direction, pos['volume'], \
                                                                         close_array[now_pos]
            return ret_signal

        if direction < 0 and close_array[now_pos] < op + direction * chart[9][now_pos-1] * atr_stop_gain:# and hp/op > 0.01:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
                                                                             1, (-1) * direction, pos['volume'], \
                                                                         close_array[now_pos]
            return ret_signal

        # if direction > 0 and close_array[now_pos] < peak_price - chart[9][now_pos - 1] * atr_stop_gain:
        #     ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
        #                                                                          1, (-1) * direction, pos['volume'], \
        #                                                                      close_array[now_pos]
        #     return ret_signal
        #
        # if direction < 0 and close_array[now_pos] > peak_price + chart[9][now_pos - 1] * atr_stop_gain:
        #     ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
        #                                                                          1, (-1) * direction, pos['volume'], \
        #                                                                      close_array[now_pos]
        #     return ret_signal



        if direction < 0 and close_array[now_pos] > np.max(high_array[now_pos-60:now_pos]):# and hp/op < -0.005:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
                                                                             1, (-1) * direction, pos['volume'], \
                                                                         close_array[now_pos]
            return ret_signal

        if direction > 0 and close_array[now_pos] < np.min(low_array[now_pos-60:now_pos]):# and hp/op < -0.005:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
                                                                             1, (-1) * direction, pos['volume'], \
                                                                         close_array[now_pos]
            return ret_signal




        # if  hp / op < -0.01:
        #     ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
        #         1, (-1) * direction, pos['volume'], close_array[now_pos]
        #     return ret_signal
        #
        if (tick[0] - pos['entry_time'] >= 60 * 60):
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = - \
                1, (-1) * direction, pos['volume'], close_array[now_pos]
            return ret_signal

    else:
        if now_pos < 1440 + 100:
            return ret_signal
        k_center = chart[10][:]
        k_low_now = k_center[now_pos] - 1.5 * chart[9][now_pos - 1]
        k_high_now = k_center[now_pos] + 1.5 * chart[9][now_pos - 1]
        k_low_last = k_center[now_pos - 1] - 1.5 * chart[9][now_pos - 2]
        k_high_last = k_center[now_pos - 1] + 1.5 * chart[9][now_pos - 2]
        b_center = k_center
        b_std_now = np.std(close_array[now_pos - 19:now_pos+1])
        b_std_last = np.std(close_array[now_pos - 20:now_pos])
        b_high_now = b_center[now_pos] + 2 * b_std_now
        b_low_now = b_center[now_pos] - 2 * b_std_now
        b_high_last = b_center[now_pos - 1] + 2 * b_std_last
        b_low_last = b_center[now_pos - 1] - 2 * b_std_last
        if b_high_now > k_high_now and b_high_last < k_high_last and close_array[now_pos] > close_array[now_pos - 5]:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = 1, 1, open_volume, \
                                                                         tick[1]
        if b_low_now < k_low_now and b_low_last > k_low_last and close_array[now_pos] < close_array[now_pos - 5]:
            ret_signal[0], ret_signal[1], ret_signal[2], ret_signal[3] = 1, -1, open_volume, \
                                                                         tick[1]




    return ret_signal
