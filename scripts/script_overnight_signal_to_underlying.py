import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime
from src.backtesting import chart, overnight

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

close_prices = {}

call_signal = {}
put_signal = {}

symbols = []

def backtest_func(symbol, index, row, signal, model_info):
    if not (symbol in symbols):
        symbols.append(symbol)
        close_prices[symbol] = []
        call_signal[symbol] = []
        put_signal[symbol] = []

    close_prices[symbol].append([index[1], row['close']])

    if index[1].hour == 19 and index[1].minute == 0:
        if signal == 'Buy':
            call_signal[symbol].append([index[1]])
        elif signal == 'Sell':
            put_signal[symbol].append([index[1]])

start = datetime(2024, 8, 1, 12, 30)
end = datetime(2024, 8, 15, 12, 30)

overnight.backtest(start, end, backtest_func, market_client)

fig = 1
for cs in symbols:
    print(f'Call signal:{len(call_signal[cs])} Put signal:{len(put_signal[cs])}')
    close_series = np.array(close_prices[cs])
    chart.chart_with_signals(close_series, call_signal[cs], put_signal[cs], f'Backtest matched {cs} signals {start}-{end}', 'Time', 'Stock price', fig)
    fig = fig + 1

# Show the plot
plt.show()