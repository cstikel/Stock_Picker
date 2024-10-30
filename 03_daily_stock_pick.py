from finvizfinance.screener.overview import Overview
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import certifi
import json
from urllib.request import urlopen
import warnings
warnings.filterwarnings("ignore")
today = datetime.today().strftime('%Y_%m_%d')

stock_scores = pd.read_csv('stock_scores/stock_score_data_recent.csv')

## Get Value Stocks

filters_dict = {'Debt/Equity':'Under 1',
                    'Operating Margin':'Positive (>0%)', 
                    'P/E':'Under 20',
                    'InsiderTransactions':'Positive (>0%)'}

foverview = Overview()
foverview.set_filter(filters_dict=filters_dict)
df_overview = foverview.screener_view()
tickers = df_overview['Ticker'].to_list()

url = 'https://valueinvestorsclub.com/ideas'
def get_trending_symbols(url):
    # Send a GET request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code != 200:
        print(f"Failed to retrieve content: {response.status_code}")
        return []

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the <b>TRENDING:</b> element
    trending_header = soup.find('b', string='TRENDING:')

    if not trending_header:
        print("No trending section found.")
        return []

    # Get the next sibling which should contain the <span> with <a> tags
    trending_span = trending_header.find_next('span')
    
    # If we found the span, extract the symbols
    symbols = []
    if trending_span:
        # Find all <a> tags with href starting with '/idea/'
        for a_tag in trending_span.find_all('a', href=lambda href: href and href.startswith('/idea/')):
            symbols.append(a_tag.text.strip())

    return symbols

# Example usage
trending_symbols = get_trending_symbols(url)

value_stocks = tickers + trending_symbols
value_stocks = list(set(value_stocks))

## Filter to value stocks

value_scores = stock_scores[stock_scores['ticker'].isin(value_stocks)]
value_scores = value_scores[['ticker', '2023', 'roce_rank', 'coef_rank', 'std_rank', 'final_rank']]

value_scores.sort_values(by='final_rank').head(5)

## Filter to stocks that are trending

#Need to make this filter more restrictive, then go into the momentem algorithm
filters_dict = {'20-Day Simple Moving Average': 'Price above SMA20', 
                '50-Day Simple Moving Average' : 'SMA50 below SMA20',
                #'200-Day Simple Moving Average': 'SMA200 below SMA50',
               "Index": 'Any' ,
               '20-Day High/Low': '0-5% below High'} #'RUSSELL 2000'
foverview = Overview()
foverview.set_filter(filters_dict=filters_dict)
df_overview = foverview.screener_view()
trending_stocks = df_overview['Ticker'].to_list()

final_stocks = value_scores[value_scores['ticker'].isin(trending_stocks)].sort_values(by='final_rank')

investing_stocks = final_stocks[final_stocks['final_rank'] <= 200]

#get current price of stocks
def get_jsonparsed_data(url):
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)
    
def get_price(tick):
    url = (f"https://financialmodelingprep.com/api/v3/quote/{tick}?apikey=PHaANSXTwW2zC5hpGFO1uhe8EkPXgio7")
    data = get_jsonparsed_data(url)
    price = data[0]['price']
    return price

investing_stocks['price_picked'] = investing_stocks['ticker'].apply(get_price)

investing_stocks['date'] = today
with open('investing_stocks.csv', 'a') as f:
    f.write('\n') 
investing_stocks.to_csv('investing_stocks.csv', mode='a', header=False, index=False)
print(investing_stocks)

print("------- End Script ----------")