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

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

totals = []

loss = 50
d = 10

shorts = []
longs = ["META"]

for j in range(5):

    for symbol in (shorts + longs):
        os.environ[f'{symbol}_STOP_LOSS'] = f'{loss}'

    end = datetime(2024, 12, 20, 12, 30)
    runner = options.BacktestOption(shorts, longs, end, 30, day_diff, market_client, trading_client, option_client)
    t, acc, sharpes = runner.run(False)

    if len(shorts) > 0:
        totals.append([t, acc, loss, float(os.getenv(f'{symbol}_GAIN_GAURD')), sharpes[shorts[0]]])
    else:
        totals.append([t, acc, loss, float(os.getenv(f'{symbol}_GAIN_GAURD')), sharpes[longs[0]]])

    loss = loss + d

df = pd.DataFrame(data=totals,columns=['total', 'accuracy', 'loss', 'gaurd', 'sharpe'])

print(df)