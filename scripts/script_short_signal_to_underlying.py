import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime
from src.backtesting import short, chart

import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

close_prices = {}

call_signal = {}
put_signal = {}
hold_signal = {}

symbols = []
positions = []

def backtest_enter(symbol, idx, row, signal, enter, model):
    index = idx[1]

    if not (symbol in symbols):
        symbols.append(symbol)
        close_prices[symbol] = []
        call_signal[symbol] = []
        put_signal[symbol] = []
        hold_signal[symbol] = []

    spot = len(close_prices[symbol]) + 1
    close_prices[symbol].append([spot, row['close']])

    if signal == 'Buy':
        call_signal[symbol].append([spot])
    elif signal == 'Sell':
        put_signal[symbol].append([spot])
    else:
        hold_signal[symbol].append([spot])

start = datetime(2024, 10, 23, 12, 30)
end = datetime(2024, 10, 24, 12, 30)

def backtest_exit(p, exit, reason, close, mv, index, pl, symbol):
    return

short.backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions)

fig = 1
for cs in symbols:
    print(f'{cs}: Call signal:{len(call_signal[cs])} Put signal:{len(put_signal[cs])} Hold signal: {len(hold_signal[cs])}')
    close_series = np.array(close_prices[cs])
    chart.chart_with_signals(close_series, call_signal[cs], put_signal[cs], f'Backtest matched {cs} signals {start}-{end}', 'Time', 'Stock price', fig)
    fig = fig + 1

# Show the plot
plt.show()