import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers.load_parameters import load_symbol_parameters
from src.helpers import get_data, features, class_model, tracker, options
from src.strats import enter, exit
from scipy.stats import norm
from src.classifiers import dip, runnup
from src.strats import short_enter

import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

params = load_symbol_parameters('../params.json')

close_prices = []

call_signal = []
put_signal = []

d_call_signal = []
d_put_signal = []

r_call_signal = []
r_put_signal = []

start = datetime(2024, 1, 1, 12, 30)
end = datetime(2024, 9, 28, 12, 30)

# From the cut off date loop every day
start_dt = start
end_dt = end
print(f'Predict start {start_dt} model end {end_dt}')

amt_days = (end - start).days
loops = int(max(math.ceil(amt_days / 20), 1))

p_st = start_dt

for l in range(loops):
    p_end = p_st + timedelta(days=30)

    print(f'Loop {l} on start {p_st} model end {p_end}')
    if p_end > end_dt:
        p_end = end_dt

    m_end = p_end - timedelta(days=1)

    print(f'Generating model up to {m_end}')
    model_info = short_enter.generate_short_models(market_client, m_end)

    for m in model_info:
        symbol = m['symbol']
        p = m['params']
        dip_model = m['dip']['model']
        runnup_model = m['runnup']['model']

        print(f'Predicting start {p_end - timedelta(days=30)}-{p_st}-{p_end}')
        pred_bars = get_data.get_bars(symbol, p_end - timedelta(days=30), p_end, market_client, 1, TimeFrameUnit.Minute)

        dip_pred_bars = features.feature_engineer_df(pred_bars.copy(), p['dip']['look_back'])
        dip_pred_bars = features.drop_prices(dip_pred_bars, p['dip']['look_back'])

        runnup_pred_bars = features.feature_engineer_df(pred_bars.copy(), p['runnup']['look_back'])
        runnup_pred_bars = features.drop_prices(runnup_pred_bars, p['runnup']['look_back'])

        for index, row in pred_bars.iterrows():
            if index[1].date() < p_st.date():
                continue

            close_prices.append([index[1], row['close']])

            dp_h = dip_pred_bars.loc[index:][:1]
            run_h = runnup_pred_bars.loc[:index][-2:]

            signals = short_enter.classify_short_signal(dp_h, run_h, m)

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

        p_st = p_end 

        if p_st > end_dt:
            break

print(f'All: {len(pred_bars)} Call signal:{len(call_signal)} Put signal:{len(put_signal)}')

close_series = np.array(close_prices)
x = close_series[:, 0]
y = close_series[:, 1]

f1 = plt.figure(1)
# Create a plot
plt.plot(x, y)

for xc in call_signal:
    plt.axvline(x=xc, color='g', linestyle='--')

for xc in put_signal:
    plt.axvline(x=xc, color='r', linestyle='--')

# Add labels and title
plt.xlabel('Time entry')
plt.ylabel('Stock price')
plt.title(f'Backtest matched signals {start}-{end}')

f2 = plt.figure(2)
# Create a plot
plt.plot(x, y)

for xc in r_call_signal:
    plt.axvline(x=xc, color='g', linestyle='--')

for xc in r_put_signal:
    plt.axvline(x=xc, color='r', linestyle='--')

# Add labels and title
plt.xlabel('Time entry')
plt.ylabel('Stock price')
plt.title(f'Backtest runnup signals {start}-{end}')

f3 = plt.figure(3)
# Create a plot
plt.plot(x, y)

for xc in d_call_signal:
    plt.axvline(x=xc, color='g', linestyle='--')

for xc in d_put_signal:
    plt.axvline(x=xc, color='r', linestyle='--')

# Add labels and title
plt.xlabel('Time entry')
plt.ylabel('Stock price')
plt.title(f'Backtest dip signals {start}-{end}')

# Show the plot
plt.show()