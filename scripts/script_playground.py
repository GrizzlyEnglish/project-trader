import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.data import options_data
from src.helpers import options, features

import numpy as np

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
polygon_key = os.getenv("POLYGON_KEY")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

symbol = 'SPY'

end = datetime(2024, 12, 6, 19)
start = end - timedelta(days=90)

od = options_data.OptionData(symbol, datetime(2024, 12, 6, 18), 'C', 608, option_client, polygon_client)

bars = od.get_bars(start, end)

bars = bars.dropna()

print('PVI increase')
for i, r in bars.iterrows():
    if r['pvi'] > .75 and r['pvi_short_trend'] > 0 and r['pvi_short_trend__last'] < 0:
        post = bars.loc[i:]
        count = 0
        for i, r2 in post.iterrows():
            if r2['close'] > (r['close'] - .02):
                count = count + 1
            else:
                print(f'{i} increased for {count} bars with')
                break

'''
print('NVI increase')
for i, r in bars.iterrows():
    if r['nvi'] > 1 and r['pvi_short_trend'] > 0 and r['pvi_short_trend__last'] < 0:
        post = bars.loc[i:]
        count = 0
        for i, r2 in post.iterrows():
            if r2['close'] < (r['close'] + .2):
                count = count + 1
            else:
                print(f'{i} decreased for {count} bars with')
                break
'''