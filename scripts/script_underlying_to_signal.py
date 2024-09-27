import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers.load_stocks import load_symbol_information
from src.helpers import get_data, features, class_model, short_classifier, tracker, options, dip_classifier
from src.strats import enter, exit
from scipy.stats import norm

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

load_dotenv()

hold_for = 1

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

symbol_info = load_symbol_information('../short_option_symbols.txt')

info = symbol_info[0]
time_window = info['time_window']
symbol = info['symbol']
day_diff = info['day_diff']
look_back = info['look_back']
look_forward = info['look_forward']

start = datetime(2024, 8, 5, 12, 30)
end = datetime(2024, 8, 6, 12, 30)

m_st = start - timedelta(days=day_diff-1)
m_end = start - timedelta(days=1)

# Generate model
print(f'Model start {m_st} model end {m_end}')
bars, call_var, put_var = class_model.get_model_bars(symbol, market_client, m_st, m_end, time_window, dip_classifier.classification, look_back, look_forward, TimeFrameUnit.Minute)
model, model_bars, accuracy, buys, sells = class_model.generate_model(symbol, bars)

# From the cut off date loop every day
start_dt = start
end_dt = end
print(f'Predict start {start_dt} model end {end_dt}')

pred_bars = get_data.get_bars(symbol, start_dt, end_dt, market_client, time_window)
pred_bars = features.feature_engineer_df(pred_bars, look_back)
pred_bars = features.drop_prices(pred_bars, look_back)

close_prices = []
loc = 0
call_signal = []
put_signal = []

call_holder = []
put_holder = []

for index, row in pred_bars.iterrows():
    close_prices.append([loc, row['close']])

    h = pred_bars.loc[index:][:1]

    if h.index != index:
        break

    pred = class_model.predict(model, h)

    if pred == 'Buy':
        call_holder.append(loc)
        if len(call_holder) == hold_for:
            call_signal.append([loc])
            call_holder = []
    elif pred == 'Sell':
        put_holder.append(loc)
        if len(put_holder) == hold_for:
            put_signal.append([loc])
            put_holder = []

    loc = loc + 1

print(f'All: {len(pred_bars)} Call signal:{len(call_signal)} Put signal:{len(put_signal)}')

close_series = np.array(close_prices)
x = close_series[:, 0]
y = close_series[:, 1]

# Create a plot
plt.plot(x, y)

for xc in call_signal:
    plt.axvline(x=xc, color='g', linestyle='--')

for xc in put_signal:
    plt.axvline(x=xc, color='r', linestyle='--')

# Add labels and title
plt.xlabel('Time entry')
plt.ylabel('Stock price')
plt.title('Backtest signals')

# Show the plot
plt.show()