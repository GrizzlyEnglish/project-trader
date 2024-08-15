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


assets = ['SPY'] 

for s in assets:
    data = []
    year = 2022
    start = datetime(year, 1, 1, 12, 30)
    model = classification.generate_model(s, market_client, start - timedelta(days=60), start - timedelta(days=1), 15)

    # Note: Get the previous bar and have it be on the same bar for more info, possibly add another indicator remove support/resistance

    while (start.year == 2022):
        start = start + timedelta(minutes=16)

        if start.weekday() <= 5 and start.hour < 21 and start.hour > 13:
            start_format = datetime.strftime(start, "%m/%d/%Y")

            bars = get_data.get_bars(s, start - timedelta(days=60), start + timedelta(hours=1), market_client, 15)
            bars = features.feature_engineer_df(bars)
            if bars.empty:
                continue

            tail = bars.tail(4)
            h = tail.head(1)
            pred = classification.predict(model, h)

            if pred != 'Hold':
                data.append({
                    'symbol': s,
                    'class': pred,
                    'date': h.index[0][1],
                    'current_price': h.iloc[0]['close'], 
                    '1_bar_later': tail.iloc[1]['close'],
                    '2_bar_later': tail.iloc[2]['close'],
                    '3_bar_later': tail.iloc[3]['close'],
                    })


df = pd.DataFrame(data)
df.to_csv('backtest.csv', index=True)