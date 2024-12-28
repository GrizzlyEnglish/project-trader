import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from polygon import RESTClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import options
from src.helpers import chart

import ast
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
day_diff = int(os.getenv('DAYDIFF'))
polygon_key = os.getenv("POLYGON_KEY")

shorts = ast.literal_eval(os.getenv('SHORT_SYMBOLS'))
longs = ast.literal_eval(os.getenv('LONG_SYMBOLS'))

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

end = datetime(2024, 12, 27, 12, 30)
start = datetime(2024, 1, 1)
days = 30#(end - start).day
runner = options.BacktestOption([], longs, end, days, day_diff, market_client, trading_client, option_client)
t = runner.run(True)
