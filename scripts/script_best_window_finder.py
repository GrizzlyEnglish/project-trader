import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import features, class_model, get_data, load_parameters
from src.classifiers import runnup, dip

import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

classification = dip.classification

save = False

assets = ['INTC']
times = [1]
days = [30]
time_unit = TimeFrameUnit.Minute
look_back_range = range(40, 50)
look_forward_range = range(45, 50)
start = datetime.now()

for symbol in assets:
    results = []

    for window in times:

        for daydiff in days:
            s = start - timedelta(days=daydiff)
            e = start + timedelta(days=1)
            full_bars = get_data.get_bars(symbol, s, e, market_client, window, time_unit)

            for back in look_back_range:
                for forward in look_forward_range:

                    look_back = back
                    look_forward = forward

                    print(f'{window},{daydiff},{look_back},{look_forward}')

                    acc = 0

                    bars = features.feature_engineer_df(full_bars.copy(), look_back)
                    bars, call_var, put_var = classification(bars, look_forward)
                    bars = features.drop_prices(bars, look_back)

                    bars, buy_count, sell_count = class_model.sample_bars(bars)

                    try:
                        model,acc = class_model.create_model(symbol, bars)
                    except:
                        print()

                    results.append([symbol, window, daydiff, back+1, forward+1, buy_count, sell_count, acc])

        df = pd.DataFrame(columns=['symbol', 'time_window', 'day diff', 'look back', 'look forward', 'buys', 'sells', 'accuracy'], data=results)
        df.to_csv(f'../results/best_window_{symbol}_{window}.csv', index=True)
        print(df)