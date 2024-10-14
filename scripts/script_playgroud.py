import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient, OptionTradesRequest, OptionBarsRequest
from alpaca.data.timeframe import TimeFrameUnit, TimeFrame
from dotenv import load_dotenv
from src.helpers import class_model
from src.classifiers import short
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

#class_model.generate_model('QQQ', 60, market_client, short.classification, datetime(2024, 7, 15, 12, 30))

odf = option_client.get_option_bars(OptionBarsRequest(symbol_or_symbols='QQQ241014C00498000', start=datetime.now() - timedelta(days=40), end=datetime.now(),timeframe=TimeFrame(1, TimeFrameUnit.Minute))).df
print(odf)