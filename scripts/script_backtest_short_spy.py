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
info = next((c for c in symbol_info if c['symbol'] == 'SPY'), None)

total_actions = 0
correct_actions = 0

time_window = info['time_window']
symbol = info['symbol']
day_diff = info['day_diff']
look_back = info['look_back']
look_forward = info['look_forward']

correct_bar_amt = math.floor(look_forward / 2)

start = datetime(2024, 9, 1, 12, 30)

wallet = 30000
wallet_series = [[start, wallet]]
purchased_series = []
sell_series = []

while (True):

    if start > datetime.now():
        break

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
    actual_labels, cv, pv = short_classifier.classification(pred_bars.copy(), look_forward)
    actual_indexes = pd.Index(actual_labels.index)

    indexes = pd.Index(pred_bars.index)

    open_contract = None

    for index, row in pred_bars.iterrows():
        strike_price = math.floor(row['close'])
        close = row['close']

        if open_contract == None:
            pred = class_model.predict(model, pd.DataFrame([row]))

            if pred == 'Hold':
                continue

            total_actions = total_actions + 1

            contract_type = 'put'
            expected_var = put_var

            if pred == 'Buy':
                contract_type = 'call'
                expected_var = call_var

            contract_price = options.get_option_price(contract_type, close, strike_price, 2, 0.05, .1181)
            if enter.check_contract_entry(index[1], contract_type, strike_price, contract_price, contract_price, .1181, 2, close, call_var):
                print(f'Purchased {contract_type} at {contract_price} with underlying at {close}')
                mv = contract_price*100
                #wallet = wallet - mv
                purchased_series.append(index[1])
                stop_loss, secure_gains = options.determine_risk_reward(mv)
                open_contract = {
                    'strike_price': strike_price,
                    'close': close,
                    'type': contract_type,
                    'price': contract_price,
                    'dte': 2,
                    'stop_loss': stop_loss,
                    'secure_gains': secure_gains
                }
            wallet_series.append([index[1], wallet])
        else:
            hst = tracker.get('SPY')
            contract_price = options.get_option_price(open_contract['type'], close, open_contract['strike_price'], open_contract['dte'], 0.05, .1181)
            mv = contract_price*100
            wallet_series.append([index[1], wallet + mv])
            exit_contract, r = exit.check_for_exit(hst, mv, open_contract['stop_loss'], open_contract['secure_gains'])

            if exit_contract:
                print(f'Sold {open_contract["type"]} for {contract_price - open_contract["price"]} underlying {close - open_contract["close"]} held for {len(hst)}')
                open_contract = None
                tracker.clear('SPY')
                wallet = wallet + mv
                sell_series.append(index[1])

            tracker.track('SPY', 0, mv)

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