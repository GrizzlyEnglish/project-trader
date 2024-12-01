import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import get_data, features

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

end = datetime(2024, 2, 29, 19)
start = end - timedelta(days=90)
df = get_data.get_bars(symbol, start, end, market_client)
df = features.feature_engineer_df(df)

end = datetime(2024, 2, 29, 19)
start = end - timedelta(days=30)
df2 = get_data.get_bars(symbol, start, end, market_client)
df2 = features.feature_engineer_df(df2)

df = df.tail(len(df2))

comparison = df != df2 
differences = df[comparison] 
differences = differences.where(comparison) 
differences = differences.dropna(axis=1, how='all')
print("Differences between DataFrames:") 
print(differences)

k1 = df['kama'][:-4]
print(k1)

k2 = df2['kama'][:-4]
print(k2)