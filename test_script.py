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

asset = 'AAPL'

now = datetime(2024, 8, 8, 17, 17)
bars = get_data.get_bars(asset, now - timedelta(days=60), now, market_client, 1)
bars = features.feature_engineer_df(bars)

short_model = class_model.create_model(asset, bars, 'short', True)
long_model = class_model.create_model(asset, bars, 'long', True)

s = datetime(2024, 8, 9, 5)
while(True):
    if s.hour == 19 and s.minute == 59:
        break

    bars = get_data.get_bars(asset, s - timedelta(days=60), s, market_client, 1)
    bars = features.feature_engineer_df(bars)

    short_pred = short_model.predict(bars.tail(1))[0]
    long_pred = long_model.predict(bars.tail(1))[0]

    print(f'{s} short: {features.int_to_label(short_pred)} long: {features.int_to_label(long_pred)}')

    s = s + timedelta(minutes=5)

print("done")