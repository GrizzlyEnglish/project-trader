import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import get_data
from classifiers import runnup
from src.backtesting import chart

import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)

close_prices = []

call_signal = []
put_signal = []

fig = 1

m_end = datetime(2024, 10, 11, 12, 30)
m_st = m_end - timedelta(days=90)

bars = get_data.get_model_bars('QQQ', market_client, m_st, m_end, 1, runnup.classification, 'Min')

bars = bars.tail(500)

for index, row in bars.iterrows():
    close_prices.append([index[1], row['close']])
    if row['label'] == 'buy':
        call_signal.append([index[1]])
    elif row['label'] == 'sell':
        put_signal.append([index[1]])

print(f'Call signal:{len(call_signal)} Put signal:{len(put_signal)}')
close_series = np.array(close_prices)
chart.chart_with_signals(close_series, call_signal, put_signal, f'Classified signals {m_st}-{m_end}', 'Time', 'Stock price', fig)
fig = fig + 1

# Show the plot
plt.show()