import asyncio
import logging
import onetoken as ot
from onetoken import Tick
from onetoken import Account, log
from TradeLib import Chart, Signal, Position
from Strategy import strategy_1
from utils import load_kline
import datetime
from pandas import Series
fh = logging.FileHandler(
    './log/' +
    datetime.datetime.now().strftime('%Y%m%d') +
    '.log')
fh.setLevel(logging.INFO)
fh.setFormatter(
    logging.Formatter(
        '%(levelname)-.4s [%(asctime)s][qb][%(filename)s:%(lineno)s] %(message)s',
        '%H:%M:%S'))
log.addHandler(fh)
log.setLevel(logging.INFO)


class TokenTrader(object):
    def __init__(self, symbol, api_key, api_secret):
        self.chart_dict = {}
        self.position_dict = {}
        self.mutex = asyncio.Lock()
        self.trading_status = {}
        self.loop = asyncio.get_event_loop()
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.account = Account(symbol, api_key, api_secret, self.loop)

    def restart(self):
        self.chart_dict = {}
        self.position_dict = {}
        self.mutex = asyncio.Lock()
        self.trading_status = {}
        self.loop = asyncio.get_event_loop()
        self.account = Account(
            self.symbol,
            self.api_key,
            self.api_secret,
            self.loop)

    def is_time_to_restart(self):
        pass

    async def get_last(self):
        while True:
            await self.mutex.acquire()
            for contract in self.chart_dict:
                tk, err = await ot.quote.get_last_tick(contract)
                if not err:
                    self.chart_dict[contract].update(tk)
                    ohlc_array = self.chart_dict[contract].to_ohlc_array()
                    # print(ohlc_array[0][self.chart_dict[contract].now_pos],
                    #       ohlc_array[1][self.chart_dict[contract].now_pos],
                    #       ohlc_array[2][self.chart_dict[contract].now_pos],
                    #       ohlc_array[3][self.chart_dict[contract].now_pos], self.chart_dict[contract].now_pos, contract)
                    #print(datetime.datetime.fromtimestamp(self.chart_dict[contract].interval_list[self.chart_dict[contract].now_pos] / 1000.0))
                else:
                    print(err)
            self.mutex.release()

    async def add_contract(self, contract, interval):
        await self.mutex.acquire()
        print('add_contract', contract)
        log.info('add_contract {}'.format(contract))
        if contract not in self.chart_dict:
            self.chart_dict[contract] = Chart(
                interval, contract, datetime.datetime.now())
        if contract not in self.trading_status:
            self.trading_status[contract] = None
        chart = load_kline(self.chart_dict[contract])
        self.chart_dict[contract] = chart
        #chart = self.chart_dict[contract]
        [o, h, l, c] = chart.to_ohlc_array()
        # print(chart.now_pos)
        # print(o[chart.now_pos])
        # print(h[chart.now_pos])
        # print(l[chart.now_pos])
        # print(c[chart.now_pos])
        print(datetime.datetime.fromtimestamp(
            chart.interval_list[chart.now_pos] / 1000.0))
        self.mutex.release()

    async def run2(self):
        contract1 = 'binance/btc.usdt'
        await self.add_contract(contract1, 1)
        while True:
            await self.get_last()
            contract2 = 'huobip/btc.usdt'
            await self.add_contract(contract2, 1)

    async def timer(self, t):
        await asyncio.sleep(t)
        print('time to change')
        contract2 = 'huobip/btc.usdt'
        await self.add_contract(contract2, 1)

    async def order_update(self, exchange_oid, loop):
        o_info_2, err = await self.account.get_order_use_exchange_oid(exchange_oid)
        if err:
            log.warning('Get order info failed...', err)
        else:
            #log.info(f'Order information by exchange_oid: {o_info_2}')
            log.info('order info received %s' % (o_info_2[0]['exchange_oid']))
        o_info_2 = o_info_2[0]
        status = o_info_2['status']
        if status in ['dealt', 'withdrawn', 'part-deal-withdrawn']:
            print('qqq')
            await self.mutex.acquire()
            if o_info_2['dealt_amount'] > 0:
                pos = Position(
                    o_info_2['contract'],
                    o_info_2['dealt_amount'],
                    o_info_2['average_dealt_price'],
                    o_info_2['entrust_price'],
                    o_info_2['entrust_time'],
                    o_info_2['bs'])
                self.position_dict[o_info_2['contract']] = pos
            self.trading_status[o_info_2['contract']] = None
            self.mutex.release()
            print('release order update')

        else:
            await asyncio.sleep(1)
            print('waiting')
            loop.create_task(self.order_update(exchange_oid, loop))

    async def close_position(self, exchange_oid, loop):
        o_info_2, err = await self.account.get_order_use_exchange_oid(exchange_oid)
        if err:
            log.warning('Get order info failed...', err)
        else:
            log.info(f'Order information by exchange_oid: {o_info_2}')
        o_info_2 = o_info_2[0]
        status = o_info_2['status']
        if status in ['dealt', 'withdrawn', 'part-deal-withdrawn']:
            pos = self.position_dict[o_info_2['contract']]
            rest_volume = pos.volume - o_info_2['dealt_amount']
            if status != 'dealt' and rest_volume > 0.001:
                price = o_info_2['entrust_price'] * \
                    1.1 if o_info_2['bs'] == 'b' else o_info_2['entrust_price'] * 0.9
                res, err = await self.account.place_and_cancel(con=o_info_2['contract'], price=round(price, 2),
                                                               bs=o_info_2['bs'],
                                                               amount=round(rest_volume, 8),
                                                               sleep=3)
                if err and err[0]:
                    log.warning('place and cancel order failed...', err)
                else:
                    log.info(f'Placed and canceled order: {res}')
                    [res1, res2] = res
                    log.info(f'{res1},{res2}')
                    loop.create_task(
                        self.close_position(
                            res[0]['exchange_oid'], loop))
            else:
                await self.mutex.acquire()
                self.position_dict[o_info_2['contract']] = None
                self.trading_status[o_info_2['contract']] = None
                self.mutex.release()
        else:
            await asyncio.sleep(1)
            print('waiting')
            loop.create_task(self.close_position(exchange_oid, loop))

    async def exec_trading(self, signal: Signal, loop):
        log.info('exec', signal)
        if signal.open_close == 'open':
            print('open signal')
            res, err = await self.account.place_and_cancel(con=signal.code, price=signal.price, bs='b' if signal.direction == 1 else 's', amount=signal.volume, sleep=10)
            if err and err[0]:
                log.warning('place and cancel order failed...', err)
            else:
                #log.info(f'Placed and canceled order: {res}')
                [res1, res2] = res
                # log.info(f'{res1},{res2}')
                log.info('open order sent%s' % (res[0]['exchange_oid']))
                loop.create_task(
                    self.order_update(
                        res[0]['exchange_oid'], loop))

        elif signal.open_close == 'close':
            print('close signal')
            res, err = await self.account.place_and_cancel(con=signal.code, price=round(signal.price, 2),
                                                           bs='b' if signal.direction == 1 else 's',
                                                           amount=signal.volume,
                                                           sleep=3)
            if err:
                log.warning('place and cancel order failed...', err)
            else:
                #log.info(f'Placed and canceled order: {res}')
                [res1, res2] = res
                # log.info(f'{res1},{res2}')
                log.info('close order sent%s' % (res[0]['exchange_oid']))
            loop.create_task(self.close_position(res[0]['exchange_oid'], loop))

    async def trading(self, loop):
        contract1 = 'binance/btc.usdt'
        await self.add_contract(contract1, 1)
        while True:
            await asyncio.sleep(5)
            info, err = await self.account.get_info()
            if err:
                log.warning('Get info failed...reconnecting', err)
            else:
                log.info(f'Account info: {info.data}')
                break

        log.info('Initialized account {}'.format(self.account))
        loop.create_task(self.get_last())
        # loop.create_task(self.timer(7))

        while True:
            await asyncio.sleep(0.5)
            await self.mutex.acquire()
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
                    log.info(signal)
                    self.trading_status[signal.code] = 'executing'
                    loop.create_task(self.exec_trading(signal, loop))
            self.mutex.release()

    def run(self):
        self.loop.run_until_complete(self.trading(self.loop))


if __name__ == '__main__':
    symbol = 'binance/l2'
    api_key = 'Dlhx30Cg-3GuDMfhi-eRnVbjpb-IeFsRKQn'
    api_secret = 'oJCMJ1xs-JctRiXAa-3F2vvYvz-W88ubT1p'
    t_trader = TokenTrader(symbol, api_key, api_secret)
    t_trader.run()
    # asyncio.get_event_loop().run_until_complete(t_trader.run())
    #loop = asyncio.get_event_loop()
