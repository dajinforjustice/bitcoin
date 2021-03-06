import asyncio
import logging
import onetoken as ot
from onetoken import Account, log
from JitTradeLib import JitInstrument, JitSignal, jit_load_kline
from strategy.volume_breaker.t3 import jit_volume_breaker_strategy

import datetime, arrow
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


class JitTokenTrader(object):
    def __init__(self, symbol, api_key, api_secret):
        self.instrument_dict = {}
        self.mutex = asyncio.Lock()
        self.loop = asyncio.get_event_loop()
        self.symbol = symbol
        self.api_key = api_key
        self.api_secret = api_secret
        self.account = Account(symbol, api_key, api_secret, self.loop)

    def restart(self):
        self.instrument_dict = {}
        self.mutex = asyncio.Lock()
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
            for contract in self.instrument_dict:
                tk, err = await ot.quote.get_last_tick(contract)
                if not err:
                    self.instrument_dict[contract].update(tk)
                    #ohlc_array = self.instrument_dict[contract].to_ohlc_array()
                    # print(ohlc_array[0][self.instrument_dict[contract].now_pos],
                    #       ohlc_array[1][self.instrument_dict[contract].now_pos],
                    #       ohlc_array[2][self.instrument_dict[contract].now_pos],
                    #       ohlc_array[3][self.instrument_dict[contract].now_pos], self.instrument_dict[contract].now_pos, contract)
                    #print(datetime.datetime.fromtimestamp(self.instrument_dict[contract].interval_list[self.instrument_dict[contract].now_pos] / 1000.0))
                else:
                    print(err)
            self.mutex.release()

    async def add_contract(self, contract, interval):
        await self.mutex.acquire()
        print('add_contract', contract)
        log.info('add_contract {}'.format(contract))
        if contract not in self.instrument_dict:
            self.instrument_dict[contract] = JitInstrument(contract, datetime.datetime.now())

        jit_load_kline(self.instrument_dict[contract])
        self.mutex.release()

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
            await self.mutex.acquire()
            if o_info_2['dealt_amount'] > 0:
                pos = self.instrument_dict[o_info_2['contract']].position
                pos['avg_price'] = o_info_2['average_dealt_price']
                pos['entry_time'] = arrow.get(o_info_2['entrust_time']).float_timestamp
                pos['direction'] = 1 if o_info_2['bs'] == 'b' else -1
                pos['status'] = 1
                pos['volume'] = o_info_2['dealt_amount']
                # pos = Position(
                #     o_info_2['contract'],
                #     o_info_2['dealt_amount'],
                #     o_info_2['average_dealt_price'],
                #     o_info_2['entrust_price'],
                #     o_info_2['entrust_time'],
                #     o_info_2['bs'])
                self.instrument_dict[o_info_2['contract']].position = pos
            self.instrument_dict[o_info_2['contract']].global_data['executing'] = 0

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
            pos = self.instrument_dict[o_info_2['contract']].position
            rest_volume = o_info_2['entrust_amount'] - o_info_2['dealt_amount']
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
                pos = self.instrument_dict[o_info_2['contract']].position
                pos['avg_price'] = 0
                pos['entry_time'] = 0
                pos['direction'] = 0
                pos['status'] = 0
                pos['volume'] = 0
                # pos = Position(
                #     o_info_2['contract'],
                #     o_info_2['dealt_amount'],
                #     o_info_2['average_dealt_price'],
                #     o_info_2['entrust_price'],
                #     o_info_2['entrust_time'],
                #     o_info_2['bs'])
                self.instrument_dict[o_info_2['contract']].position = pos
                self.instrument_dict[o_info_2['contract']].global_data['executing'] = 0
                self.mutex.release()
        else:
            await asyncio.sleep(1)
            print('waiting')
            loop.create_task(self.close_position(exchange_oid, loop))

    async def exec_trading(self, signal: JitSignal, loop):
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

            for code, instrument in self.instrument_dict.items():

                signal = jit_volume_breaker_strategy(instrument.last_tick, instrument.chart, instrument.position,
                                      instrument.global_data)
                if abs(signal[0]) > 1e-9:
                    exec_signal = JitSignal(code, signal)
                    signals.add(exec_signal)

            for signal in signals:
                if self.instrument_dict[signal.code].global_data['executing'] < 1:
                    log.info(signal)
                    self.instrument_dict[signal.code].global_data['executing'] = 1
                    loop.create_task(self.exec_trading(signal, loop))

            self.mutex.release()

    def run(self):
        self.loop.run_until_complete(self.trading(self.loop))


if __name__ == '__main__':
    symbol = 'binance/l2'
    api_key = 'Dlhx30Cg-3GuDMfhi-eRnVbjpb-IeFsRKQn'
    api_secret = 'oJCMJ1xs-JctRiXAa-3F2vvYvz-W88ubT1p'
    t_trader = JitTokenTrader(symbol, api_key, api_secret)
    t_trader.run()
    # asyncio.get_event_loop().run_until_complete(t_trader.run())
    #loop = asyncio.get_event_loop()
