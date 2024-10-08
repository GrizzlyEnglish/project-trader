import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime
from src.backtesting import short, chart

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

d_call_signal = {}
d_put_signal = {}

r_call_signal = {}
r_put_signal = {}

symbols = []

def backtest_func(symbol, index, row, signals, model_info):
    if not (symbol in symbols):
        symbols.append(symbol)
        close_prices[symbol] = []
        call_signal[symbol] = []
        put_signal[symbol] = []
        d_call_signal[symbol] = []
        d_put_signal[symbol] = []
        r_call_signal[symbol] = []
        r_put_signal[symbol] = []

    close_prices[symbol].append([index[1], row['close']])

    sig = signals['signal']
    run_sig = signals['runnup']
    dip_sig = signals['dip']

    if sig == 'Buy':
        call_signal[symbol].append([index[1]])
    elif sig == 'Sell':
        put_signal[symbol].append([index[1]])

    if dip_sig == 'Buy':
        d_call_signal[symbol].append([index[1]])
    elif dip_sig == 'Sell':
        d_put_signal[symbol].append([index[1]])

    for r in run_sig:
        if r == 'Buy':
            r_call_signal[symbol].append([index[1]])
        elif r == 'Sell':
            r_put_signal[symbol].append([index[1]])

start = datetime(2024, 10, 1, 12, 30)
end = datetime(2024, 10, 9, 12, 30)

short.backtest(start, end, backtest_func, market_client)

fig = 1
for cs in symbols:
    print(f'Call signal:{len(call_signal[cs])} Put signal:{len(put_signal[cs])}')
    close_series = np.array(close_prices[cs])
    chart.chart_with_signals(close_series, call_signal[cs], put_signal[cs], f'Backtest matched {cs} signals {start}-{end}', 'Time', 'Stock price', fig)
    fig = fig + 1
    chart.chart_with_signals(close_series, r_call_signal[cs], r_put_signal[cs], f'Backtest RUNNUP {cs} signals {start}-{end}', 'Time', 'Stock price', fig)
    fig = fig + 1
    chart.chart_with_signals(close_series, d_call_signal[cs], d_put_signal[cs], f'Backtest DIP {cs} signals {start}-{end}', 'Time', 'Stock price', fig)
    fig = fig + 1

# Show the plot
plt.show()