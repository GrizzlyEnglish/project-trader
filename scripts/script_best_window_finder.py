import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.strats import short_enter
from src.helpers import features, load_stocks, class_model, get_data, short_classifier

import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

save = False

assets = ['GOOGL']
times = [1]
days = [7, 14, 30]
look_back_range = range(10, 15)
look_forward_range = range(55, 60)

for symbol in assets:
    results = []

    for window in times:

        for daydiff in days:
            start = datetime(2024, 8, 29, 12, 30)
            s = start - timedelta(days=daydiff)
            e = start + timedelta(days=1)
            full_bars = get_data.get_bars(symbol, s, e, market_client, window, TimeFrameUnit.Minute)

            for back in look_back_range:
                for forward in look_forward_range:

                    look_back = back
                    look_forward = forward

                    print(f'{window},{daydiff},{look_back},{look_forward}')

                    if window == 1 and daydiff > 30:
                        continue

                    acc = 0
                    buy_count = 0
                    sell_count = 0

                    bars = features.feature_engineer_df(full_bars.copy(), look_back)
                    bars = short_classifier.classification(bars, look_forward)
                    bars = features.drop_prices(bars, look_back)

                    try:
                        model, model_bars, accuracy, buys, sells = class_model.generate_model(symbol, bars)
                        acc = accuracy
                        buy_count = buys
                        sell_count = sells
                    except:
                        print()

                    results.append([symbol, window, daydiff, back+1, forward+1, buy_count, sell_count, acc])

        df = pd.DataFrame(columns=['symbol', 'time_window', 'day diff', 'look back', 'look forward', 'buys', 'sells', 'accuracy'], data=results)
        df.to_csv(f'best_window_{symbol}_{window}.csv', index=True)
        print(df)