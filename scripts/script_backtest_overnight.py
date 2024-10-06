import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, time, timezone

from src.backtesting import overnight, chart, strats

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

start = datetime(2024, 1, 1, 12, 30)
end = datetime(2024, 10, 2, 12, 30)

close_series = {}
telemetry = []
symbols = []
pl_series = []

open_contract = {}
actions = 0
correct_actions = 0

def backtest_func(symbol, index, row, signal, model_info):
    global actions, correct_actions

    if not (symbol in open_contract):
        open_contract[symbol] = None
        close_series[symbol] = []
        symbols.append(symbol)

    if (index[1].hour == 19 and index[1].minute == 0):
        if signal == 'Buy':
            open_contract[symbol] = { "type": "call", "symbol": symbol, "close": row["close"], "time": index[1]}
            actions = actions + 1
        elif signal == 'Sell':
            open_contract[symbol] = { "type": "put", "symbol": symbol, "close": row["close"], "time": index[1]}
            actions = actions + 1
    elif open_contract[symbol] != None and index[1].hour == 13:
        con = open_contract[symbol]
        if con["time"].date() < index[1].date():
            if (row["close"] > con["close"] and con["type"] == "call") or (row["close"] < con["close"] and con["type"] == "put"):
                con['correct'] = True 
                correct_actions = correct_actions + 1
            else:
                con['correct'] = False
            con["next_close"] = row["close"]
            telemetry.append(con)
            pl_series.append([con['type'], row['close'] - con['close']])
            open_contract[symbol] = None

overnight.backtest(start, end, backtest_func, market_client)

print(f'Accuracy {correct_actions/actions}')

pd.DataFrame(data=telemetry).to_csv(f'../results/overnight_backtest.csv', index=True)

pl_series = np.array(pl_series)
x = [float(p) for p in pl_series[:, 1]]
y = pl_series[:, 0]
categories = [f'{y[i]} {i+1}' for i in range(len(y))]

plt.bar(categories, x, color=['orange' if 'call' in value else 'purple' for value in y])

plt.xlabel('Option type')
plt.ylabel('P/L')
plt.title('Option backtest p/l')

# Show the plot
plt.show()