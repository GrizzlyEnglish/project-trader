from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers import get_data, class_model, features
from datetime import datetime, timedelta

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

asset = 'SPY'

now = datetime(2024, 8, 1, 13)
bars = get_data.get_bars(asset, now - timedelta(days=120), now, market_client, 15)
bars = features.feature_engineer_df(bars)

short_model = class_model.create_model(asset, bars, 'short', 15, 'generated/classification/SPY', True)
#long_model = class_model.create_model(asset, bars, 'long', True)

s = datetime(2024, 8, 9, 19)

bars = get_data.get_bars(asset, s - timedelta(days=120), s, market_client, 15)
bars = features.feature_engineer_df(bars)

bars = bars.tail(30)

for index in range(len(bars)):
    bar = bars[index:index+1] 
    short_pred = short_model.predict(bar)
    short_pred = [features.int_to_label(p) for p in short_pred]

    if all(x == short_pred[0] for x in short_pred) and short_pred[0] != 'Hold':
        print(f'{bar.index} short: {short_pred}')