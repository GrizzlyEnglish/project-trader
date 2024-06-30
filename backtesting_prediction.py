from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.trend_logic import get_predicted_price
from helpers.get_data import get_bars
from datetime import datetime, timedelta

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

indexes = [[], []] 
data = []

holding = {}

assets = [
    'QQQ'
]

year = 2024

for asset in assets:
    start = datetime(year, 1, 1, 12, 30)

    data = []

    while (start.year == 2024):
        weekday = start.weekday()
        if weekday <= 5:
            print(start)

            predicted = get_predicted_price(asset, market_client, start)

            if predicted != None:
                diff = 1

                if weekday == 4:
                    diff = 3

                actual = get_bars(asset, start, start + timedelta(days=1), market_client)

                if not actual.empty:
                    actual = actual.iloc[-1]['close']
                    data.append({
                        'date': start,
                        'predicted': predicted,
                        'actual': actual
                    })

        start = start + timedelta(days=1)

        if start.date() == datetime.now().date():
            break

    df = pd.DataFrame(data)
    df.to_csv('backtest.csv', index=True)