import pandas as pd
from finvizfinance.quote import finvizfinance

indexes = [	'DJIA', 'QQQ', 'SPY', 'IWM']

def str_to_num(input):
    x = float(input.strip('%')) / 100
    return x

def invest_market(input):
    if input > 0:
        x = "Investable"
    else:
        x = "Avoid"

    return x

intervals = {'Near' : 'SMA20',
              'Med ' : 'SMA50',
              'Long' : 'SMA200'}

for ind in indexes:
    print(f'------------ {ind} ------------')
    stock = finvizfinance(ind)
    stock_fundament = stock.ticker_fundament()
    for i in intervals:
        level = intervals[i]
        avoid = invest_market(str_to_num(stock_fundament[level]))
        print(f'  {i} ------- {avoid}')
    print("")