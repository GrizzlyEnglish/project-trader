import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import features
from src.data import bars_data

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

symbol = 'SPY'
delta = float(os.getenv(f'{symbol}_DELTA'))
end = datetime(2024, 11, 29, 19)
start = end - timedelta(days=365)
bars_handlers = bars_data.BarData(symbol, start, end, market_client)
df = bars_handlers.get_bars(1, 'Min')
df['indicator'] = df.apply(features.my_indicator, axis=1)

dates = np.unique(df.index.get_level_values('timestamp').date)

up_vars = []
down_vars = []

diff = 25

for index, row in df.iterrows(): 
    if row['indicator'] != 0: 
        idx = row.name[1]
        idx = idx + timedelta(minutes=diff)
        index = (symbol, idx)

        while not index in df.index:
            idx = idx + timedelta(minutes=1)
            index = (symbol, idx)

        bar = df.loc[index]
        var =bar['close'] - row['close'] 

        if row['indicator'] == 1:
            up_vars.append(var)
        else:
            down_vars.append(var)
            
print(f'Indicators up: {len(up_vars)} down: {len(down_vars)}')
print(f'average difference for {diff} minutes on {symbol}')
print(f'up mean {np.array(up_vars).mean()} max {np.array(up_vars).max()} min {np.array(up_vars).min()}')
print(f'down mean {np.array(down_vars).mean()} max {np.array(down_vars).max()} min {np.array(down_vars).min()}')