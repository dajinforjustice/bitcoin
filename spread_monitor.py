import asyncio

import onetoken as ot
from onetoken import Tick

global last_binance
global last_huobi

def on_update(tk: Tick):
    global last_binance
    global last_huobi
    print('tick come', tk)
    if tk.contract == 'binance/btc.usdt':
        last_binance = tk.last
    if tk.contract == 'huobip/btc.usdt':
        last_huobi = tk.last


def on_update2(tk: Tick):
    print('tick come 2', tk)


async def sub_func():
    contract = 'binance/btc.usdt'
    await ot.quote.subscribe_tick(contract, on_update)

    contract = 'huobip/btc.usdt'
    await ot.quote.subscribe_tick(contract, on_update2)

    #contract = 'okex/eth.btc'
    #await ot.quote.subscribe_tick(contract, on_update2)


async def get_last():
    contract = 'binance/btc.usdt'
    contract2 = 'huobip/btc.usdt'
    global last_huobi
    global last_binance
    last_huobi = 0
    last_binance = 0
    while True:
        #await asyncio.sleep(2)
        tk, err = await ot.quote.get_last_tick(contract)
        if not err:
            last_binance = tk.last
        tk, err = await ot.quote.get_last_tick(contract2)
        if not err:
            last_huobi = tk.last
        #print(last_huobi - last_binance)
        #print(tk.time.strftime.)
        print(tk, err)



async def main():
    #await sub_func()
    await get_last()



if __name__ == '__main__':
    import logging

    print('ots folder', ot)
    ot.log_level(logging.INFO)
    asyncio.get_event_loop().run_until_complete(main())
