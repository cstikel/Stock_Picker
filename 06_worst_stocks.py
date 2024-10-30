from finvizfinance.screener.overview import Overview
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
import certifi
import json
from urllib.request import urlopen
today = datetime.today().strftime('%Y_%m_%d')

stock_scores = pd.read_csv('stock_scores/stock_score_data_recent.csv')

filters_dict = {'Debt/Equity':'Over 1',
                    #'Operating Margin':'Negative (<0%)', 
                    'P/E': 'Over 5'}

foverview = Overview()
foverview.set_filter(filters_dict=filters_dict)
df_overview = foverview.screener_view()
tickers = df_overview['Ticker'].to_list()

non_value_scores = stock_scores[stock_scores['ticker'].isin(tickers)]
non_value_scores = non_value_scores[['ticker', '2023', 'roce_rank', 'coef_rank', 'std_rank', 'final_rank']]

non_value_scores

filters_dict = {'20-Day Simple Moving Average': 'Price below SMA20', 
                '50-Day Simple Moving Average' : 'SMA50 above SMA20',
                #'200-Day Simple Moving Average': 'SMA200 below SMA50',
               "Index": 'Any'} #'RUSSELL 2000'
foverview = Overview()
foverview.set_filter(filters_dict=filters_dict)
df_overview = foverview.screener_view()
trending_stocks = df_overview['Ticker'].to_list()

final_stocks = non_value_scores[non_value_scores['ticker'].isin(trending_stocks)].sort_values(by='final_rank')
short_stocks = final_stocks[final_stocks['final_rank'] >= 1200]
def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)
    
def get_price(tick):
    url = (f"https://financialmodelingprep.com/api/v3/quote/{tick}?apikey=PHaANSXTwW2zC5hpGFO1uhe8EkPXgio7")
    data = get_jsonparsed_data(url)
    price = data[0]['price']
    return price

short_stocks['price_picked'] = short_stocks['ticker'].apply(get_price)


short_stocks['date'] = today
with open('short_stocks.csv', 'a') as f:
    f.write('\n') 
short_stocks.to_csv('short_stocks.csv', mode='a', header=False, index=False)

print(short_stocks)



print("-------- End of Script --------")