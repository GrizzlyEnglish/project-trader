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
from src.options import buy

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


bars_handlers = bars_data.BarData('QQQ', datetime.now() - timedelta(days=90), datetime.now(), market_client)

mbars = bars_handlers.get_bars(1, 'Min')
mbars['short_indicator'] = mbars.apply(features.short_indicator, axis=1)

hbars = bars_handlers.get_bars(1, 'Hour')
hbars['long_indicator'] = hbars.apply(features.long_indicator, axis=1)

mbars = mbars[mbars['short_indicator'] != 0]
hbars = hbars[hbars['long_indicator'] != 0]

print('t')