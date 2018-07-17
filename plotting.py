# encoding: UTF-8
import os
import datetime
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import matplotlib.pyplot as plt
import numpy as np
#from utils import MA


def _candlestick(
        ax,
        ohlc_array,
        width=0.2,
        color_up='r',
        color_down='g',
        alpha=1.0):
    offset = width / 2.0
    lines = []
    patches = []
    t = 0
    for i in range(len(ohlc_array[0])):
        t += 1
        op, high, low, close = ohlc_array[0][i], ohlc_array[1][i], ohlc_array[2][i], ohlc_array[3][i]
        if close >= op:
            color = color_up
            lower = op
            height = close - op
        else:
            color = color_down
            lower = close
            height = op - close

        vline = Line2D(
            xdata=(t, t), ydata=(low, high),
            color=color,
            linewidth=0.5,
            antialiased=True,
        )

        rect = Rectangle(
            xy=(t - offset, lower),
            width=width,
            height=height,
            facecolor=color,
            edgecolor=color,
        )
        rect.set_alpha(alpha)

        lines.append(vline)
        patches.append(rect)
        ax.add_line(vline)
        ax.add_patch(rect)
    ax.autoscale_view()
    return lines, patches

def plot_price_indicator_ret(close_array, indicator_array, ret_array, save_path):
    x = np.arange(len(close_array))
    zero = np.zeros(len(close_array))
    ax = plt.subplot(311)
    plt.plot(x, close_array)
    ax.autoscale_view()

    ax = plt.subplot(312)
    plt.plot(x, indicator_array)
    plt.plot(x, zero)
    ax.autoscale_view()

    ax = plt.subplot(313)
    plt.plot(x, ret_array)
    ax.autoscale_view()

    if save_path:
        plt.savefig(os.path.join(save_path))
        plt.clf()
        plt.close()
    else:
        plt.show()


def draw_pic(date, ohlc_array, volume_array, save_path, ret_array):
    #fig, ax = plt.subplots(3,1,True)
    ax = plt.subplot(311)
    # fig.subplots_adjust(bottom=0.2)
    _candlestick(ax, ohlc_array, width=0.6, color_up='r', color_down='g')
    # for i in lines:
    #     plt.plot([i[0], i[1]], [i[2], i[3]], color='green', linewidth=1, linestyle="-")
    ax.autoscale_view()
    plt.setp(
        plt.gca().get_xticklabels(),
        rotation=45,
        horizontalalignment='right')
    # ax.grid(True)
    #plt.savefig(os.path.join(save_path, date+".jpg"))
    # plt.clf()
    # plt.close()
    #fig, ax2 = plt.subplots(212)
    ax = plt.subplot(312)
    x = np.arange(len(volume_array))
    plt.bar(x, volume_array)
    ax.autoscale_view()
    ax = plt.subplot(313)
    plt.plot(x, ret_array)
    ax.autoscale_view()
    plt.title(date)
    if save_path:
        plt.savefig(os.path.join(save_path))
        plt.clf()
        plt.close()


def draw_kline(date, ohlc_array, lines, save_path):
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.2)
    fig.set_size_inches(204.8, 153.6)

    for i in lines:
        color = ''
        width = 1
        if i[-1] == 30:
            color = 'black'
            width = 2
        elif i[-1] == 60:
            color = 'mediumblue'
            width = 3
        if i[-1] == 240:
            color = 'blueviolet'
            width = 4
        if i[-1] == 1440:
            color = 'orange'
            width = 5
        plt.plot([i[0], i[1]], [i[2], i[3]], color=color,
                 linewidth=width, linestyle="-")
    _candlestick(ax, ohlc_array, width=0.6, color_up='r', color_down='g')
    ax.autoscale_view()
    plt.setp(
        plt.gca().get_xticklabels(),
        rotation=45,
        horizontalalignment='right')
    ax.grid(True)
    plt.title(date)

    plt.savefig(os.path.join(save_path, date + ".jpg"))
    plt.clf()
    plt.close()


def fig_analysis(
        para1,
        para2,
        para3,
        para4,
        para5,
        open_array,
        high_array,
        low_array,
        close_array,
        pre_day_high_array,
        pre_day_low_array,
        pre_day_close_array,
        day_start_array,
        day_end_array,
        ret_array,
        day_list):

    save_path = os.path.join(
        './fig', datetime.datetime.now().strftime('%y%m%d_%H%M%S'))
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    ma60 = np.zeros(len(pre_day_high_array), dtype='f8')
    ma10 = np.zeros(len(pre_day_high_array), dtype='f8')
    ma5 = np.zeros(len(pre_day_high_array), dtype='f8')
    ma60 = MA(pre_day_close_array, ma60, 60)
    ma10 = MA(pre_day_close_array, ma10, 10)
    ma5 = MA(pre_day_close_array, ma5, 5)
    for day in range(1, len(day_start_array)):
        day_start = day_start_array[day]
        day_end = day_end_array[day]
        day_long = day_end - day_start
        today_open_array = open_array[day_start:day_end]
        today_high_array = high_array[day_start:day_end]
        today_low_array = low_array[day_start:day_end]
        today_close_array = close_array[day_start:day_end]
        Ssetup = pre_day_high_array[day] + para1 * \
            (pre_day_close_array[day] - pre_day_low_array[day])
        Bsetup = pre_day_low_array[day] - para1 * \
            (pre_day_high_array[day] - pre_day_close_array[day])

        Senter = (1 + para3) / 2 * \
            (pre_day_high_array[day] + pre_day_low_array[day]) - para3 * pre_day_low_array[day]
        Benter = (1 + para3) / 2 * \
            (pre_day_high_array[day] + pre_day_low_array[day]) - para3 * pre_day_high_array[day]

        Sbreak = Bsetup - para2 * (Ssetup - Bsetup)
        Bbreak = Ssetup + para2 * (Ssetup - Bsetup)

        ohlc_array = [
            today_open_array,
            today_high_array,
            today_low_array,
            today_close_array]

        lines = []
        lines.append((0, day_long, Bbreak, Bbreak))
        lines.append((0, day_long, Ssetup, Ssetup))
        lines.append((0, day_long, Senter, Senter))
        lines.append((0, day_long, Benter, Benter))
        lines.append((0, day_long, Bsetup, Bsetup))
        lines.append((0, day_long, Sbreak, Sbreak))

        if int(ret_array[5][day]) != 0:
           # lines.append((stat[3],stat[4],stat[1],stat[2]))
            lines.append(
                (int(
                    ret_array[1][day]), int(
                    ret_array[2][day]), int(
                    ret_array[3][day]), int(
                    ret_array[4][day])))

        draw_pic(day_list[day], ohlc_array, lines, save_path)


def rbreaker_data(high, low, close, paras):
    [para1, para2, para3, para4, para5] = paras
    Ssetup = high + para1 * (close - low)
    Bsetup = low - para1 * (high - close)
    Senter = (1 + para3) / 2 * (high + low) - para3 * low
    Benter = (1 + para3) / 2 * (high + low) - para3 * high
    Sbreak = Bsetup - para2 * (Ssetup - Bsetup)
    Bbreak = Ssetup + para2 * (Ssetup - Bsetup)
    return Bbreak, Ssetup, Senter, Benter, Bsetup, Sbreak


def plot_ret_and_price(ret_array, price_array):
    # np.random.seed(2000)
    #date = np.random.standard_normal((20, 2))
    #y = date.cumsum(axis=0)
    # plt.figure()
    #y[:, 0] = y[:, 0] * 100
    fig, ax1 = plt.subplots()
    plt.plot(ret_array, 'b', label="return")
    #plt.plot(y[:, 0], 'ro')

    plt.grid(True)
    plt.axis('tight')
    plt.xlabel("time index")
    plt.ylabel('return')
    #plt.title("This is double axis label")

    plt.legend(loc=0)

    ax2 = ax1.twinx()
    plt.plot(price_array, 'g', label="price")
    #plt.plot(y[:, 1], 'r*')
    plt.ylabel("price")
    plt.legend(loc=1)

    plt.show()


def gen_lines(ohlc_array, paras):
    [tmp_open_array, tmp_high_array, tmp_low_array, tmp_close_array] = ohlc_array
    lines = []
    intervals = [30, 60, 240, 1440]
    for interval in intervals:
        for index in range(interval, len(tmp_high_array), interval):
            h = tmp_high_array[index - interval:index].max()
            l = tmp_low_array[index - interval:index].min()
            c = tmp_close_array[index - 1]
            Bbreak, Ssetup, Senter, Benter, Bsetup, Sbreak = rbreaker_data(
                h, l, c, paras)
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Bbreak, Bbreak, interval])
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Ssetup, Ssetup, interval])
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Senter, Senter, interval])
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Benter, Benter, interval])
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Bsetup, Bsetup, interval])
            lines.append([index, min(index + interval - 1,
                                     len(tmp_close_array)), Sbreak, Sbreak, interval])
    return lines
