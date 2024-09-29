import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from src.helpers import tracker, options
from src.strats import enter, exit
from datetime import datetime

from src.backtesting import short, chart

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
end = datetime(2024, 9, 26, 12, 30)

close_series = []
purchased_series = []
sell_series = []
pl_series = []
telemetry = []
option_telemetry = []
vol = 0.5
r = 0.05
dte = 2

def check_for_entry(signal, close_price, call_var, put_var, index, strike_price):
    global vol, r, dte

    if signal['signal'] == 'Hold':
        return

    contract_type = 'put'
    expected_var = put_var

    if signal['signal'] == 'Buy':
        contract_type = 'call'
        expected_var = call_var

    contract_price = options.get_option_price(contract_type, close_price, strike_price, dte, r, vol)
    if enter.check_contract_entry(index, contract_type, strike_price, contract_price, contract_price, vol, r, dte, close_price, expected_var):
        print(f'Purchased {contract_type} at {contract_price} with underlying at {close_price} with r {r} and vol {vol}')
        mv = contract_price*100
        purchased_series.append(index)
        stop_loss, secure_gains = options.determine_risk_reward(mv)
        return {
            'strike_price': strike_price,
            'close': close_price,
            'type': contract_type,
            'price': contract_price,
            'dte': dte,
            'stop_loss': stop_loss,
            'market_value': mv,
            'secure_gains': secure_gains,
            'bought_at': index
        }

    return None

def check_for_exit(symbol, close_price, index, open_contract):
    global vol, r

    hst = tracker.get(symbol)
    contract_price = options.get_option_price(open_contract['type'], close_price, open_contract['strike_price'], open_contract['dte'], r, vol)
    mv = contract_price*100
    exit_contract, reason = exit.check_for_exit(hst, mv, open_contract['stop_loss'], open_contract['secure_gains'])

    if exit_contract:
        print(f'Sold {symbol} {open_contract["type"]} for profit of {contract_price - open_contract["price"]} underlying {close_price - open_contract["close"]} held for {len(hst)}')
        tracker.clear(symbol)
        sell_series.append(index)
        return True, mv, reason

    tracker.track(symbol, 0, mv)
    return False, mv, ''

open_contract = {}

def backtest_func(symbol, idx, row, signal, model_info):
    index = idx[1]

    if not (symbol in open_contract):
        open_contract[symbol] = None

    call_var = model_info['runnup']['call_variance']
    put_var = model_info['runnup']['put_variance']

    close = row['close']
    close_series.append([index, close])

    strike_price = math.floor(close)

    if open_contract[symbol] == None:
        con = check_for_entry(signal, close, call_var, put_var, index, strike_price)
        open_contract[symbol] = con
    else:
        open_contract[symbol]['dte'] = open_contract[symbol]['dte'] - 0.003
        if open_contract[symbol]['dte'] <= 0:
            do_exit = True
            mv = open_contract[symbol]['prev_mv']
        else:
            do_exit, mv, reason = check_for_exit(symbol, close, index, open_contract[symbol])
            open_contract[symbol]['prev_mv'] = mv
        if do_exit:
            tel = {
                'symbol': symbol,
                'strike_price': strike_price,
                'sold_close': close,
                'bought_close': open_contract[symbol]['close'],
                'type': open_contract[symbol]['type'],
                'bought_price': open_contract[symbol]['market_value'],
                'sold_price': mv,
                'stop_loss': open_contract[symbol]['stop_loss'],
                'secure_gains': open_contract[symbol]['secure_gains'],
                'bought_at': open_contract[symbol]['bought_at'],
                'sold_at': index,
                'held_for': index - open_contract[symbol]['bought_at'],
                'sold_for': reason
            }
            telemetry.append(tel)
            open_contract[symbol] = None
            pl_series.append([tel['type'], (tel['sold_price'] - tel['bought_price'])])
        else:
            tel = {
                'symbol': symbol,
                'strike_price': open_contract[symbol]['strike_price'],
                'sold_close': close,
                'bought_at': open_contract[symbol]['bought_at'],
                'at': index,
                'market_value': mv
            }
            option_telemetry.append(tel)


short.backtest(start, end, backtest_func, market_client)

pd.DataFrame(data=telemetry).to_csv(f'../results/backtest.csv', index=True)
pd.DataFrame(data=option_telemetry).to_csv(f'../results/backtest_tel.csv', index=True)

# Separate the data into x and y
close_series = np.array(close_series)

chart.chart_with_signals(close_series, purchased_series, sell_series, f'Backtest {start}-{end}', 'Time', 'Cash', 1)

fig = plt.figure(2)

pl_series = np.array(pl_series)
x = [float(p) for p in pl_series[:, 1]]
y = pl_series[:, 0]
categories = [f'{y[i]} {i+1}' for i in range(len(y))]

plt.bar(categories, x, color=['orange' if 'call' in value else 'purple' for value in y])

plt.xlabel('P/L')
plt.ylabel('Times')
plt.title('Simple Bar Graph')

# Show the plot
plt.show()