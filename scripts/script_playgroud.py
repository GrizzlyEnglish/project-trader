import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient, OptionTradesRequest, OptionBarsRequest
from alpaca.data.timeframe import TimeFrameUnit, TimeFrame
from dotenv import load_dotenv
from src.helpers import class_model, get_data, options, features
from datetime import datetime, timedelta

import os
import numpy as np
from scipy.optimize import newton

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

df = options.get_bars('SPY241023P00578000', datetime(2024, 10, 23, 16, 24), datetime(2024, 10, 24), option_client)
print(df)