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

close_prices = []

call_signal = []
put_signal = []

d_call_signal = []
d_put_signal = []

r_call_signal = []
r_put_signal = []

def backtest_func(index, row, signals):
    close_prices.append([index[1], row['close']])

    sig = signals['signal']
    run_sig = signals['runnup']
    dip_sig = signals['dip']

    if sig == 'Buy':
        call_signal.append([index[1]])
    elif sig == 'Sell':
        put_signal.append([index[1]])

    if dip_sig == 'Buy':
        d_call_signal.append([index[1]])
    elif dip_sig == 'Sell':
        d_put_signal.append([index[1]])

    for r in run_sig:
        if r == 'Buy':
            r_call_signal.append([index[1]])
        elif r == 'Sell':
            r_put_signal.append([index[1]])

start = datetime(2024, 9, 15, 12, 30)
end = datetime(2024, 9, 26, 12, 30)

short.backtest(start, end, backtest_func, market_client)

print(f'Call signal:{len(call_signal)} Put signal:{len(put_signal)}')

close_series = np.array(close_prices)

chart.chart_with_signals(close_series, call_signal, put_signal, f'Backtest matched signals {start}-{end}', 'Time', 'Stock price', 1)
chart.chart_with_signals(close_series, r_call_signal, r_put_signal, f'Backtest RUNNUP signals {start}-{end}', 'Time', 'Stock price', 2)
chart.chart_with_signals(close_series, d_call_signal, d_put_signal, f'Backtest DIP signals {start}-{end}', 'Time', 'Stock price', 3)

# Show the plot
plt.show()