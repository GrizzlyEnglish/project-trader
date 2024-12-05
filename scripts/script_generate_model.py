import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from src.strategies import trending_model
from src.helpers import get_data, features, class_model
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
delta = float(os.getenv('HIGH_RISK_DELTA'))

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

model_end = datetime(2024, 10, 1, 20)

model = trending_model.TrendingModel('SPY', model_end, 90, 600, market_client)

knn = model.generate_model()

end = datetime(2024, 11, 29, 20)
test_bars = get_data.get_bars('SPY', end - timedelta(days=30), end, market_client)
test_bars = features.feature_engineer_df(test_bars)

total_action = 1
pred_correct_action = 1
ind_correct_action = 1
b_correct_action = 1 

dates = np.unique(test_bars.index.get_level_values('timestamp').date)
for dt in dates:
    if dt > model_end.date():
        dtstr = dt.strftime("%Y-%m-%d")
        day_bars = test_bars.loc[('SPY', dtstr)].copy()

        day_bars['indicator'] = day_bars.apply(features.my_indicator, axis=1)

        for index, row in day_bars.iterrows(): 
            if row['indicator'] != 0:
                r = row.drop('indicator')
                pred = knn.predict([r])

                pred = class_model.int_to_label(pred)

                post = day_bars.loc[row.name:]
                first = features.max_or_min_first(np.array(post['close']), delta, row['close'])

                ind = 'sell' if row['indicator'] == -1 else 'buy'
                pred_acc = 'correct' if pred == 'sell' and row['close'] > first else 'incorrect'
                ind_acc = 'correct' if ind == 'sell' and row['close'] > first else 'incorrect'
                pred_correct_action = pred_correct_action + (1 if pred_acc == 'correct' else 0)
                ind_correct_action = ind_correct_action + (1 if ind_acc == 'correct' else 0)
                total_action = total_action + 1
                b_correct_action = b_correct_action + (1 if ind != pred and pred_acc == 'correct' and ind_acc == 'correct' else 0)
                print(f'{row.name} indicator:{ind}/{ind_acc} prediction: {pred}/{pred_acc} {row["close"]} {first}')

print(f'pred acc {pred_correct_action/(pred_correct_action+total_action)}')
print(f'ind acc {ind_correct_action/(ind_correct_action+total_action)}')
print(f'both acc {b_correct_action/(b_correct_action+total_action)}')