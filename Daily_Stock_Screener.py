from finvizfinance.screener.overview import Overview
from finvizfinance.quote import finvizfinance
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, date
import certifi
import json
from urllib.request import urlopen
import warnings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
warnings.filterwarnings("ignore")

def get_trending_symbols(url):
    """Scrape trending symbols from ValueInvestorsClub"""
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve content: {response.status_code}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    trending_header = soup.find('b', string='TRENDING:')

    if not trending_header:
        print("No trending section found.")
        return []

    trending_span = trending_header.find_next('span')
    symbols = []
    
    if trending_span:
        for a_tag in trending_span.find_all('a', href=lambda href: href and href.startswith('/idea/')):
            symbols.append(a_tag.text.strip())

    return symbols

def get_jsonparsed_data(url):
    """Parse JSON data from URL"""
    response = urlopen(url, cafile=certifi.where())
    data = response.read().decode("utf-8")
    return json.loads(data)
    
def get_price(tick):
    """Get current price for a ticker"""
    url = (f"https://financialmodelingprep.com/api/v3/quote/{tick}?apikey=PHaANSXTwW2zC5hpGFO1uhe8EkPXgio7")
    data = get_jsonparsed_data(url)
    price = data[0]['price']
    return price

def get_value_stocks(stock_scores):
    """Get value stocks based on fundamental criteria"""
    filters_dict = {
        'Debt/Equity': 'Under 1',
        'Operating Margin': 'Positive (>0%)',
        'P/E': 'Under 20',
        'InsiderTransactions': 'Positive (>0%)'
    }
    
    foverview = Overview()
    foverview.set_filter(filters_dict=filters_dict)
    df_overview = foverview.screener_view()
    tickers = df_overview['Ticker'].to_list()
    
    url = 'https://valueinvestorsclub.com/ideas'
    trending_symbols = get_trending_symbols(url)
    
    value_stocks = list(set(tickers + trending_symbols))
    
    value_scores = stock_scores[stock_scores['ticker'].isin(value_stocks)]
    return value_scores[['ticker', '2023', 'roce_rank', 'coef_rank', 'std_rank', 'final_rank']]

def get_non_value_stocks(stock_scores):
    """Get non-value stocks based on fundamental criteria"""
    filters_dict = {
        'Debt/Equity': 'Over 1',
        'P/E': 'Over 5'
    }
    
    foverview = Overview()
    foverview.set_filter(filters_dict=filters_dict)
    df_overview = foverview.screener_view()
    tickers = df_overview['Ticker'].to_list()
    
    non_value_scores = stock_scores[stock_scores['ticker'].isin(tickers)]
    return non_value_scores[['ticker', '2023', 'roce_rank', 'coef_rank', 'std_rank', 'final_rank']]

def get_market_analysis():
    """Get market analysis for major indexes"""
    indexes = ['DJIA', 'QQQ', 'SPY', 'IWM']
    market_data = []
    
    def str_to_num(input):
        x = float(input.strip('%')) / 100
        return x
    
    def invest_market(input):
        if input > 0:
            return "Investable"
        return "Avoid"
    
    intervals = {
        'Near  - 1 Month': 'SMA20',
        'Med   - 3 Month': 'SMA50',
        'Long  - 1 Year ': 'SMA200'
    }
    
    for ind in indexes:
        index_data = [f'Index: {ind}']
        stock = finvizfinance(ind)
        stock_fundament = stock.ticker_fundament()
        for interval, level in intervals.items():
            avoid = invest_market(str_to_num(stock_fundament[level]))
            index_data.append(f'  {interval} ------- {avoid}')
        market_data.extend(index_data)
        market_data.append("")  # Add blank line between indexes
        
    return market_data

def format_email_body(investing_stocks, short_stocks):
    """Format the email body with market analysis, long and short positions"""
    def format_dataframe(df):
        """Helper function to format individual DataFrames"""
        df_display = df[['ticker', 'roce_rank', 'coef_rank', 'final_rank']].copy()
        df_display = df_display.round(0)
        df_display.columns = ['TKR', 'ROCE', 'COEF', 'RANK']
        
        numeric_cols = df_display.select_dtypes(include=['float64']).columns
        for col in numeric_cols:
            df_display[col] = df_display[col].map('{:.0f}'.format)
        
        return df_display.to_string(
            index=False,
            justify='left',
            col_space={
                'TKR': 6,
                'ROCE': 6,
                'COEF': 6,
                'RANK': 6
            }
        )

    email_body = []
    
    # Add header with date
    email_body.append(f"Stock Analysis - {datetime.today().strftime('%b %d, %Y')}")
    email_body.append("=" * 35)
    email_body.append("")

    # Add market analysis section
    email_body.append("MARKET ANALYSIS")
    email_body.append("-" * 15)
    market_data = get_market_analysis()
    email_body.extend(market_data)
    email_body.append("")

    # Add long positions section
    email_body.append("LONG POSITIONS")
    email_body.append("-" * 15)
    if len(investing_stocks) > 0:
        email_body.append(format_dataframe(investing_stocks))
    else:
        email_body.append("No long positions identified today.")
    email_body.append("")
    
    # Add summary statistics for long positions
    if len(investing_stocks) > 0:
        email_body.append(f"Total: {len(investing_stocks)}")
        email_body.append(f"Avg Rank: {investing_stocks['final_rank'].mean():.0f}")
        email_body.append("")

    # Add short positions section
    email_body.append("SHORT POSITIONS")
    email_body.append("-" * 15)
    if len(short_stocks) > 0:
        email_body.append(format_dataframe(short_stocks))
    else:
        email_body.append("No short positions identified today.")
    email_body.append("")
    
    # Add summary statistics for short positions
    if len(short_stocks) > 0:
        email_body.append(f"Total: {len(short_stocks)}")
        email_body.append(f"Avg Rank: {short_stocks['final_rank'].mean():.0f}")
        email_body.append("")

    # Add footer
    email_body.append("-" * 35)
    email_body.append("Auto-generated report - Do not reply")
    
    return "\n".join(email_body)

def send_email(to_emails, subject_body, email_body, from_email, password, smtp_server="smtp.gmail.com", smtp_port=587):
    """Send email with stock analysis results to multiple recipients"""
    # Convert single email to list if necessary
    if isinstance(to_emails, str):
        to_emails = [to_emails]
        
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = f"{date.today().strftime('%Y-%m-%d')} Auto-Generated Stock Picks"
    
    # Create email body with monospace font for better table formatting
    email_text = f"""
<pre style="font-family: Courier New, Courier, monospace;">
{email_body}
</pre>
"""
    msg.attach(MIMEText(email_text, "html"))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        
        # Send to all recipients
        server.sendmail(from_email, to_emails, msg.as_string())
        print(f"Email sent successfully to {len(to_emails)} recipients!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        server.quit()

def main():
    today = datetime.today().strftime('%Y_%m_%d')
    stock_scores = pd.read_csv('stock_scores/stock_score_data_recent.csv')
    
    # Process value stocks (long positions)
    value_scores = get_value_stocks(stock_scores)
    
    long_filters = {
        '20-Day Simple Moving Average': 'Price above SMA20',
        '50-Day Simple Moving Average': 'SMA50 below SMA20',
        'Index': 'Any',
        '20-Day High/Low': '0-5% below High'
    }
    
    foverview = Overview()
    foverview.set_filter(filters_dict=long_filters)
    df_overview = foverview.screener_view()
    trending_stocks = df_overview['Ticker'].to_list()
    
    final_stocks = value_scores[value_scores['ticker'].isin(trending_stocks)].sort_values(by='final_rank')
    investing_stocks = final_stocks[final_stocks['final_rank'] <= 250]
    
    # Get prices and save long positions
    investing_stocks['price_picked'] = investing_stocks['ticker'].apply(get_price)
    investing_stocks['date'] = today
    
    with open('investing_stocks.csv', 'a') as f:
        f.write('\n')
    investing_stocks.to_csv('investing_stocks.csv', mode='a', header=False, index=False)
    print("Long Positions:")
    print(investing_stocks)
    
    # Process non-value stocks (short positions)
    non_value_scores = get_non_value_stocks(stock_scores)
    
    short_filters = {
        '20-Day Simple Moving Average': 'Price below SMA20',
        '50-Day Simple Moving Average': 'SMA50 above SMA20',
        'Index': 'Any'
    }
    
    foverview = Overview()
    foverview.set_filter(filters_dict=short_filters)
    df_overview = foverview.screener_view()
    trending_stocks = df_overview['Ticker'].to_list()
    
    final_stocks = non_value_scores[non_value_scores['ticker'].isin(trending_stocks)].sort_values(by='final_rank')
    short_stocks = final_stocks[final_stocks['final_rank'] >= 2200]
    
    # Get prices and save short positions
    short_stocks['price_picked'] = short_stocks['ticker'].apply(get_price)
    short_stocks['date'] = today
    
    with open('short_stocks.csv', 'a') as f:
        f.write('\n')
    short_stocks.to_csv('short_stocks.csv', mode='a', header=False, index=False)
    print("\nShort Positions:")
    print(short_stocks)
    
    # Send email with results
    to_emails = [
        "kristen.anderson08@gmail.com",
        "Chas.stikes@gmail.com"
        #"johnstonryan@mac.com",
        #"hgediriweera@gmail.com",
        #"austin.black89@gmail.com"
    ]
    subject_body = f"{date.today().strftime('%Y-%m-%d')} Auto-Generated Stock Picks"
    email_body = format_email_body(investing_stocks, short_stocks)
    from_email = "funnyfarmcapital@gmail.com"
    password = "wrxf zbqb ycsy bozj" 
    
    send_email(to_emails, subject_body, email_body, from_email, password)
    
    print("\n-------- End of Script --------")

if __name__ == "__main__":
    main()