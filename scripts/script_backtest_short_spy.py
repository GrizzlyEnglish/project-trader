import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers.load_stocks import load_symbol_information
from src.helpers import get_data, features, class_model, short_classifier, tracker, options
from src.strats import enter, exit

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

symbol_info = load_symbol_information('../short_option_symbols.txt')
#symbol_info = [c for c in symbol_info if c['symbol'] == 'SPY']

start = datetime(2024, 8, 1, 12, 30)

wallet = 30000
wallet_series = [[start, wallet]]
purchased_series = []
sell_series = []
telemetry = []

def check_for_entry(model, call_var, put_var, index):
    pred = class_model.predict(model, row)

    if pred == 'Hold':
        return

    contract_type = 'put'
    expected_var = put_var

    if pred == 'Buy':
        contract_type = 'call'
        expected_var = call_var

    contract_price = options.get_option_price(contract_type, close, strike_price, 2, 0.05, .1181)
    if enter.check_contract_entry(index, contract_type, strike_price, contract_price, contract_price, .1181, 2, close, expected_var):
        print(f'Purchased {contract_type} at {contract_price} with underlying at {close}')
        mv = contract_price*100
        purchased_series.append(index)
        stop_loss, secure_gains = options.determine_risk_reward(mv)
        return {
            'strike_price': strike_price,
            'close': close,
            'type': contract_type,
            'price': contract_price,
            'dte': 2,
            'stop_loss': stop_loss,
            'market_value': mv,
            'secure_gains': secure_gains,
            'bought_at': index
        }

    return None

def check_for_exit(symbol, index, open_contract):
    hst = tracker.get(symbol)
    contract_price = options.get_option_price(open_contract['type'], close, open_contract['strike_price'], open_contract['dte'], 0.05, .1181)
    mv = contract_price*100
    exit_contract, r = exit.check_for_exit(hst, mv, open_contract['stop_loss'], open_contract['secure_gains'])

    if exit_contract:
        print(f'Sold {symbol} {open_contract["type"]} for profit of {contract_price - open_contract["price"]} underlying {close - open_contract["close"]} held for {len(hst)}')
        tracker.clear(symbol)
        sell_series.append(index)
        return True, mv

    tracker.track(symbol, 0, mv)
    return False, mv

while (True):

    if start > datetime.now():
        break

    backtest_holder = {}
    open_contract = {}
    done_count = 0
    done = {}

    for info in symbol_info:
        time_window = info['time_window']
        symbol = info['symbol']
        day_diff = info['day_diff']
        look_back = info['look_back']
        look_forward = info['look_forward']

        st = start - timedelta(days=day_diff-1)
        end = start - timedelta(days=1)

        # Generate model
        print(f'Model start {st} model end {end}')
        bars, call_var, put_var = class_model.get_model_bars(symbol, market_client, st, end, time_window, short_classifier.classification, look_back, look_forward, TimeFrameUnit.Minute)
        model, model_bars, accuracy, buys, sells = class_model.generate_model(symbol, bars)

        # From the cut off date loop every day
        start_dt = start
        end_dt = start + timedelta(days=31)
        print(f'Predict start {start_dt} model end {end_dt}')

        pred_bars = get_data.get_bars(symbol, start_dt, end_dt, market_client, time_window)
        pred_bars = features.feature_engineer_df(pred_bars, look_back)
        pred_bars = features.drop_prices(pred_bars, look_back)

        # Setup labels to see if the signal matched
        #actual_labels, cv, pv = short_classifier.classification(pred_bars.copy(), look_forward)
        #actual_indexes = pd.Index(actual_labels.index)

        backtest_holder[symbol] = {
            'model': model,
            'pred_bars': pred_bars,
            'call_var': call_var,
            'put_var': put_var,
            'loc': 0
        }
        open_contract[symbol] = None
        done[symbol] = False

    while (done_count < len(symbol_info)):
        wallet_at_time = wallet
        for info in symbol_info:
            symbol = info['symbol']

            if done[symbol]:
                continue

            holder = backtest_holder[symbol]
            loc = holder['loc']
            pred_bars = holder['pred_bars']
            model = holder['model']

            if loc == len(pred_bars):
                done[symbol] = True
                done_count = done_count + 1
                continue

            row = pred_bars.iloc[loc:loc+1]
            close = row.iloc[0]['close']

            strike_price = math.floor(close)
            index = row.index[0][1]

            if open_contract[symbol] == None:
                con = check_for_entry(model, holder['call_var'], holder['put_var'], index)
                open_contract[symbol] = con
            else:
                do_exit, mv = check_for_exit(symbol, index, open_contract[symbol])
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
                        'held_for': index - open_contract[symbol]['bought_at']
                    }
                    telemetry.append(tel)
                    open_contract[symbol] = None
                    wallet = wallet + mv
                wallet_at_time = wallet_at_time + mv

            holder['loc'] = holder['loc'] + 1

        wallet_series.append([index, wallet_at_time])

    start = start + timedelta(days=31)

    print(wallet)

# Separate the data into x and y
wallet_series = np.array(wallet_series)
x = wallet_series[:, 0]
y = wallet_series[:, 1]

# Create a plot
plt.plot(x, y)

for xc in purchased_series:
    plt.axvline(x=xc, color='r', linestyle='--')

for xc in sell_series:
    plt.axvline(x=xc, color='g', linestyle='--')

# Add labels and title
plt.xlabel('Time')
plt.ylabel('Cash')
plt.title('Backtest options')

# Show the plot
plt.show()

pd.DataFrame(data=telemetry).to_csv(f'../results/backtest.csv', index=True)