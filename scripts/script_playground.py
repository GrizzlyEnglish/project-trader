import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.data import options_data

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

od = options_data.OptionData(symbol, datetime(2024, 2, 29, 12), datetime(2024, 2, 29, 18), 'C', 280, option_client, polygon_client)
print(od.symbol)

od = options_data.OptionData(symbol, datetime(2024, 2, 29, 13), datetime(2024, 2, 29, 18), 'C', 280, option_client, polygon_client)
print(od.symbol)

od = options_data.OptionData(symbol, datetime(2024, 2, 29, 14), datetime(2024, 2, 29, 18), 'C', 280, option_client, polygon_client)
print(od.symbol)

od = options_data.OptionData(symbol, datetime(2024, 2, 28, 14), datetime(2024, 2, 29, 18), 'C', 280, option_client, polygon_client)
print(od.symbol)
