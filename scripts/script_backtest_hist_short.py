import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, time, timezone, timedelta

from src.backtesting import short, chart
from src.helpers import options, features

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
option_client = OptionHistoricalDataClient(api_key, api_secret)

end = datetime(2024, 10, 12, 12, 30)
start = end - timedelta(days=7)

close_series = {}
purchased_series = {}
sell_series = {}
pl_series = []
telemetry = []
symbols = []
vol = 0.5
r = 0.05
dte = 3
open_contract = {}
actions = 0
correct_actions = 0

o_tel = []

def create_option_symbol(underlying, dte, call_put, strike):
    strike_formatted = f"{strike:08.3f}".replace('.', '').rjust(8, '0')
    date = dte.strftime("%y%m%d")
    option_symbol = f"{underlying}{date}{call_put}{strike_formatted}"
    
    return option_symbol

def backtest_func(symbol, idx, row, signal, enter, model):
    global actions, correct_actions, open_contract

    index = idx[1]

    if not (symbol in open_contract):
        open_contract[symbol] = None
        close_series[symbol] = []
        purchased_series[symbol] = []
        sell_series[symbol] = []
        symbols.append(symbol)

    market_open = datetime.combine(index, time(13, 30), timezone.utc)
    market_close = datetime.combine(index, time(19, 1), timezone.utc)

    if index <= market_open or index >= market_close:
        return

    close = row['close']
    close_series[symbol].append([index, close])

    strike_price = math.floor(close)

    if open_contract[symbol] == None and enter:
        type = 'P'
        contract_type = 'put'
        if signal == 'Buy':
            type = 'C'
            contract_type = 'call'

        contract_symbol = create_option_symbol(symbol, index, type, strike_price)

        bars = options.get_bars(contract_symbol, index - timedelta(hours=1), index, option_client)

        if bars.empty:
            return

        contract_price = bars['close'].iloc[-1]

        if contract_price > 0:
            open_contract[symbol] = {
                'contract_symbol': contract_symbol,
                'contract_type': contract_type,
                'strike_price': strike_price,
                'close': close,
                'price': contract_price,
                'market_value': contract_price * 100,
                'dte': dte,
                'bought_at': index,
                'date_of': index.date()
            }
            purchased_series[symbol].append(index)
    elif open_contract[symbol] != None:
        open_contract[symbol]['dte'] = open_contract[symbol]['dte'] - 0.003
        held_for = index - open_contract[symbol]['bought_at']

        bars = options.get_bars(open_contract[symbol]['contract_symbol'], index - timedelta(hours=1), index, option_client)
        mv = 0
        if not bars.empty:
            mv = bars['close'].iloc[-1] * 100

        pl = mv - open_contract[symbol]['market_value']
        pld = features.get_percentage_diff(open_contract[symbol]['market_value'], mv)

        reason = ''

        if (signal == 'sell' and open_contract[symbol]['contract_type'] == 'call') or (signal == 'buy' and open_contract[symbol]['contract_type'] == 'put'):
            reason = 'reversal'

        if index.hour == 19:
            reason = 'market close'

        #if held_for >= timedelta(minutes=15) and pld < 0:
            #reason = 'too long' 

        if held_for >= timedelta(minutes=15) and not bars.empty:
            o_tel.append({
                'symbol': open_contract[symbol]['contract_symbol'],
                'bar_close': bars['close'].iloc[-1]
            })

        if pld >= 30:
            reason = 'secure gains'

        if pld <= -25:
            reason = 'stop loss'
        
        if index.date() > open_contract[symbol]['date_of']:
            reason = 'expired'

        if reason != '':
            tel = {
                'symbol': symbol,
                'strike_price': open_contract[symbol]['strike_price'],
                'sold_close': close,
                'bought_close': open_contract[symbol]['close'],
                'type': open_contract[symbol]['contract_type'],
                'bought_price': open_contract[symbol]['market_value'],
                'sold_price': mv,
                'bought_at': open_contract[symbol]['bought_at'],
                'sold_at': index,
                'held_for': open_contract[symbol]['bought_at'] - index,
                'sold_for': reason,
                'pl': pl
            }
            sell_series[symbol].append(index)
            telemetry.append(tel)
            pl_series.append([tel['type'], (tel['sold_price'] - tel['bought_price'])])
            actions = actions + 1
            if pl > 0 or mv == 0:
                correct_actions = correct_actions + 1
            open_contract[symbol] = None


short.backtest(start, end, backtest_func, market_client)

print(f'Accuracy {correct_actions/actions}')

pd.DataFrame(data=telemetry).to_csv(f'../results/short_backtest.csv', index=True)
pd.DataFrame(data=o_tel).to_csv(f'../results/option_telemetry.csv', index=True)

for cs in symbols:
    pd.DataFrame(data=purchased_series[cs]).to_csv(f'../results/{cs}_short_backtest_purchases.csv', index=True)
    pd.DataFrame(data=sell_series[cs]).to_csv(f'../results/{cs}_short_backtest_sells.csv', index=True)

# Separate the data into x and y
fig = 1
for cs in symbols:
    c_series = np.array(close_series[cs])
    ps = purchased_series[cs]
    ss = sell_series[cs]
    chart.chart_with_signals(c_series, ps, ss, f'Backtest {start}-{end}', 'Time', 'Close', fig)
    fig = fig + 1

fig = plt.figure(fig)

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