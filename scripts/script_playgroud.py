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

df = options.get_bars('SPY241114P00595000', datetime(2024, 11, 14, 17, 12), datetime(2024, 11, 15), option_client)
print(df)