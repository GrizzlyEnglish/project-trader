from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strats import classification
from helpers import get_data, features
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbols

import os
import pandas as pd
import numpy as np

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

#assets = load_symbols('option_symbols.txt')
assets = ['spy']

data = []
accuracies = []
time_window = 30

for year in [2022, 2023]:
    for s in assets:
        start = datetime(year, 1, 1, 12, 30)
        model = classification.generate_model(s, market_client, start - timedelta(days=60), start - timedelta(days=1), time_window)

        bars = get_data.get_bars(s, datetime(year, 1, 1) - timedelta(days=60), datetime(year, 12, 31), market_client, time_window)
        bars = features.feature_engineer_df(bars)

        indexes = pd.Index(bars.index)

        total_actions = 0
        correct_actions = 0

        for index,row in bars.iterrows():
            if index[1].month == 1:
                start_idx = indexes.get_loc(index)
                bars = bars[start_idx:]
                break

        for index, row in bars.iterrows():
            h = bars.loc[[index]]
            h_pred = features.drop_prices(h.copy())
            pred = classification.predict(model, h_pred)

            if pred != 'Hold':
                total_actions = total_actions + 1

                price = row['close']
                loc = indexes.get_loc(index) + 4
                next_price = -1

                if loc < len(bars):
                    next_price = bars.iloc[loc]['close']

                if (pred == 'Buy' and price < next_price and next_price != -1) or (pred == 'Sell' and price > next_price and next_price != -1):
                    correct_actions = correct_actions + 1

                data.append({
                    'symbol': s,
                    'class': pred,
                    'date': index[1],
                    'current_price': price, 
                    'later_price': next_price,
                    })
        
        acc = correct_actions / total_actions
        accuracies.append({
            'symbol': s,
            'accuracy': acc,
            'year': year
        })

dfa = pd.DataFrame(accuracies)
dfa.to_csv('backtest_acc.csv', index=True)

df = pd.DataFrame(data)
df.to_csv('backtest.csv', index=True)