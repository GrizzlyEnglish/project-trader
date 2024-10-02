import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from src.helpers import tracker, options
from src.strats import enter, exit
from datetime import datetime, time, timezone

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

start = datetime(2024, 9, 1, 12, 30)
end = datetime(2024, 10, 2, 12, 30)

close_series = {}
purchased_series = {}
sell_series = {}
pl_series = []
telemetry = []
option_telemetry = []
symbols = []
vol = 0.5
r = 0.05
dte = 1

def check_for_entry(signal, close_price, call_var, put_var, index, strike_price, symbol, look_forward):
    global vol, r, dte

    if signal['signal'] == 'Hold':
        return

    contract_type = 'put'
    expected_var = put_var

    if signal['signal'] == 'Buy':
        contract_type = 'call'
        expected_var = call_var

    contract_price = options.get_option_price(contract_type, close_price, strike_price, dte, r, vol)
    if enter.check_contract_entry(index, contract_type, strike_price, contract_price, contract_price, vol, r, dte, close_price, expected_var, look_forward):
        print(f'Purchased {contract_type} at {contract_price} with underlying at {close_price} with r {r} and vol {vol}')
        mv = contract_price*100
        purchased_series[symbol].append(index)
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

def check_for_exit(symbol, close_price, index, open_contract, signal):
    global vol, r

    hst = tracker.get(symbol)
    contract_price = options.get_option_price(open_contract['type'], close_price, open_contract['strike_price'], open_contract['dte'], r, vol)
    mv = contract_price*100
    exit_contract, reason = exit.check_for_exit(hst, open_contract['type'], signal, mv, open_contract['stop_loss'], open_contract['secure_gains'])

    if exit_contract:
        print(f'Sold {symbol} {open_contract["type"]} for profit of {contract_price - open_contract["price"]} underlying {close_price - open_contract["close"]} held for {len(hst)}')
        tracker.clear(symbol)
        sell_series[symbol].append(index)
        return True, mv, reason

    tracker.track(symbol, 0, mv)
    return False, mv, ''

open_contract = {}
actions = 0
correct_actions = 0

def backtest_func(symbol, idx, row, signal, model_info):
    global actions, correct_actions, open_contract

    index = idx[1]

    if not (symbol in open_contract):
        open_contract[symbol] = None
        close_series[symbol] = []
        purchased_series[symbol] = []
        sell_series[symbol] = []
        symbols.append(symbol)

    market_open = datetime.combine(index, time(13, 0), timezone.utc)
    market_close = datetime.combine(index, time(19, 1), timezone.utc)

    if index <= market_open or index >= market_close:
        return

    call_var = model_info['runnup']['call_variance']
    put_var = model_info['runnup']['put_variance']

    close = row['close']
    close_series[symbol].append([index, close])

    strike_price = math.floor(close)

    if open_contract[symbol] == None:
        con = check_for_entry(signal, close, call_var, put_var, index, strike_price, symbol, model_info['params']['runnup']['look_forward'])
        open_contract[symbol] = con
    else:
        open_contract[symbol]['dte'] = open_contract[symbol]['dte'] - 0.003
        if open_contract[symbol]['dte'] <= 0.6:
            do_exit = True
            mv = open_contract[symbol]['prev_mv']
            reason = 'expired'
        else:
            do_exit, mv, reason = check_for_exit(symbol, close, index, open_contract[symbol], signal)
            if mv > 0:
                open_contract[symbol]['prev_mv'] = mv
            else:
                print("why")
        if index.hour == 19:
            do_exit = True
            reason = 'market close'
        if do_exit:
            pl = mv - open_contract[symbol]['market_value']
            tel = {
                'symbol': symbol,
                'strike_price': open_contract[symbol]['strike_price'],
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
                'sold_for': reason,
                'pl': pl
            }
            telemetry.append(tel)
            pl_series.append([tel['type'], (tel['sold_price'] - tel['bought_price'])])
            actions = actions + 1
            if pl > 0 or mv == 0:
                correct_actions = correct_actions + 1
            open_contract[symbol] = None
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

print(f'Accuracy {correct_actions/actions}')

pd.DataFrame(data=telemetry).to_csv(f'../results/backtest.csv', index=True)
pd.DataFrame(data=option_telemetry).to_csv(f'../results/backtest_tel.csv', index=True)

# Separate the data into x and y
for cs in symbols:
    c_series = np.array(close_series[cs])
    ps = purchased_series[cs]
    ss = sell_series[cs]
    chart.chart_with_signals(c_series, ps, ss, f'Backtest {start}-{end}', 'Time', 'Close', 1)

fig = plt.figure(2)

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