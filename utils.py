from api.client import Client
from TradeLib import Chart
import datetime

def load_kline(chart: Chart):
    client = Client('','')
    code = ''.join(chart.code.split('/')[-1].split('.')).upper()
    fetched_data = client.get_klines(symbol=code, interval='1m')
    for data in fetched_data:
        start_time = data[0]
        end_time = data[6]
        #print(datetime.datetime.fromtimestamp(start_time/1000.0).strftime('%Y %m %d %H %M %S'))
        for index in range(len(chart.interval_list)-1):
            #print(datetime.datetime.fromtimestamp(chart.interval_list[index] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(chart.interval_list[index+1] / 1000.0).strftime('%Y%m%d %H%M%S'),
            #      datetime.datetime.fromtimestamp(start_time / 1000.0).strftime('%Y%m%d %H%M%S'))
            if start_time >= chart.interval_list[index] and end_time <= chart.interval_list[index+1]:
                #print(chart.interval_list[index], start_time, end_time)
                chart.bars[index].open = data[1]
                chart.bars[index].high = data[2]
                chart.bars[index].low = data[3]
                chart.bars[index].close = data[4]
                chart.bars[index].volume = data[5]
                chart.now_pos = index
    print (chart.code ,' load done')
    return chart
