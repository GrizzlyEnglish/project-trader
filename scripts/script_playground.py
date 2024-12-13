import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.data import options_data, bars_data
from src.helpers import options, features
from src.strategies import short_option

import numpy as np
import pandas as pd

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

data = options_data.OptionData('QQQ', datetime.now(), 'C', 571, option_client)
data.set_symbol('QQQ240102C00403000')
o_bars = data.get_bars(datetime.now() - timedelta(days=365), datetime.now())

bars_handlers = bars_data.BarData('QQQ', datetime(2024,1,2), datetime(2024,1,3), market_client)
bars = bars_handlers.get_bars(1, 'Min')

print(bars)
print(o_bars)