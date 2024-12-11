import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from polygon import RESTClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import options_short
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
symbols = ast.literal_eval(os.getenv('SYMBOLS'))
polygon_key = os.getenv("POLYGON_KEY")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

totals = []

loss = 40
gains = 40
gaurd = 0.01
d = 1
symbol = 'QQQ'

for i in range(5):
    gaurd = 0.01
    for j in range(5):
        os.environ[f'{symbol}_SECURE_GAINS'] = f'{gains}'
        os.environ[f'{symbol}_STOP_LOSS'] = f'{loss}'
        os.environ[f'{symbol}_GAIN_GAURD'] = f'{gaurd}'

        end = datetime(2024, 12, 9, 12, 30)
        runner = options_short.BacktestOptionShort([symbol], end, 90, day_diff, market_client, trading_client, option_client)
        t, acc = runner.run(False)

        totals.append([t, acc, loss, gains, gaurd])

        gains = gains + d
        loss = loss + d
        gaurd = gaurd + .01

df = pd.DataFrame(data=totals,columns=['total', 'accuracy', 'loss', 'gains', 'gaurd'])

print(df)