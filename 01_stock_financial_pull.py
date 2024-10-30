import pandas as pd
import time 
from datetime import datetime
from finvizfinance.screener.overview import Overview
import warnings
warnings.filterwarnings("ignore")

today = datetime.today().strftime('%Y_%m_%d')

indexes = ['S&P 500', 'NASDAQ 100', 'DJIA', 'RUSSELL 2000']
tickers = []
for ind in indexes:
    filters_dict = {'Index' : ind}
    foverview = Overview()
    foverview.set_filter(filters_dict=filters_dict)
    df_overview = foverview.screener_view()
    temp_tickers = df_overview['Ticker'].to_list()
    tickers = tickers + temp_tickers

tickers = list(set(tickers))

import certifi
import json
from urllib.request import urlopen

def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)

year_now = datetime.now().year
main_df = pd.DataFrame()

for ticks in tickers:


    url = (f"https://financialmodelingprep.com/api/v3/ratios/{ticks}?period=quarter&apikey=PHaANSXTwW2zC5hpGFO1uhe8EkPXgio7")
    data = get_jsonparsed_data(url)

    dict = {'ticker' : [],
                'year' : [],
                'period' : [],
                'roce' : []}
    
    for i in range(len(data)):
        symbol = data[i]['symbol']
        roce = data[i]['returnOnCapitalEmployed']
        period = data[i]['period']
        year =  data[i]['calendarYear']
    
        dict['ticker'].append(symbol)
        dict['year'].append(year)
        dict['period'].append(period)
        dict['roce'].append(roce)

    df = pd.DataFrame(dict)
    df = df.groupby(by=['ticker','year']).agg({'roce':'sum', 'period': 'count'})
    df['adjusted_roce'] = (df['roce'] / df['period'] ) * 4
    df.reset_index(inplace=True)
    df = df[(pd.to_numeric(df['year']) >= (year_now-10)) & (pd.to_numeric(df['year']) <= year_now)]
    transposed_df = df.pivot(index='ticker', columns='year', values='roce')
    transposed_df.reset_index(inplace=True)
    main_df = pd.concat([main_df, transposed_df])
    #time.sleep(0.01)

main_df.to_csv(f"stock_financials/ROCE_Ratios_{today}.csv")
main_df.to_csv(f"stock_financials/ROCE_Ratios_recent.csv")