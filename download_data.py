# -*- coding: utf-8 -*-
from urllib import request
import json
import gzip
from datetime import datetime, timedelta
import os
from JitTradeLib import load_binance_code


def uncompress_file(fn_in, fn_out):
    f_in = gzip.open(fn_in, 'rb')
    f_out = open(fn_out, 'wb')
    file_content = f_in.read()
    f_out.write(file_content)
    f_out.close()
    f_in.close()


def download_contract(exchange, contract, date_start, date_end):

    trading_pair = contract

    while date_start < date_end:

        date_start_str = date_start.strftime('%Y-%m-%d')
        try:
            os.makedirs(
                os.path.join(
                    './data_json/',
                    exchange,
                    trading_pair,
                    date_start_str))
        except BaseException:
            pass
        url = "http://alihz-net-0.qbtrade.org/hist-ticks?date=%s&contract=%s/%s&format=json" % (
            date_start_str, exchange, trading_pair)
        # print(url)
        try:
            response = request.urlopen(url)
            page = response.read()
            fn_in = os.path.join(
                './data_json/',
                exchange,
                trading_pair,
                date_start_str,
                date_start_str + '.gz')
            fn_out = os.path.join(
                './data_json/',
                exchange,
                trading_pair,
                date_start_str,
                date_start_str +
                '.json')
            fin = open(fn_in, 'wb')
            fin.write(page)
            fin.close()
            uncompress_file(fn_in, fn_out)
            print(exchange, trading_pair, date_start_str, 'done')
        except Exception as e:
            print(e)
            print(exchange, trading_pair, date_start_str, 'fail')
        date_start += timedelta(days=1)
        # data = []
        # for line in open(fn_out, 'r'):
        #     data.append(json.loads(line))

if __name__ == '__main__':
    path = './txt/binance.code.txt'
    codes = load_binance_code(path)
    date_start = datetime(2018, 5, 1)
    date_end = datetime(2018, 5, 24)
    exchange = 'binance'
    #trading_pair = 'btc.usdt'
    flag = 1
    for code in codes:
        trading_pair = code.split('/')[1]
        trading_pair = 'trx.btc'
        print(trading_pair)

        if trading_pair == 'trx.btc':
            flag = 1
        if flag:
            download_contract(exchange, trading_pair, date_start, date_end)
        break
