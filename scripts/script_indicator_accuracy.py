import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import features
from src.data import bars_data

import numpy as np
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
polygon_key = os.getenv("POLYGON_KEY")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

symbol = 'QQQ'
delta = float(os.getenv(f'{symbol}_DELTA'))
end = datetime(2024, 11, 29, 19)
start = end - timedelta(days=365)
bars_handlers = bars_data.BarData(symbol, start, end, market_client)
df = bars_handlers.get_bars(1, 'Min')
df['indicator'] = df.apply(features.my_indicator, axis=1)

actions = 0
p_correct = 0
c_correct = 0
calls = 0
puts = 0
incorrect_bars = []
correct_bars = []
dates = np.unique(df.index.get_level_values('timestamp').date)
for dt in dates:
    dtstr = dt.strftime("%Y-%m-%d")
    day_bars = df.loc[(symbol, dtstr)]

    for index, row in day_bars.iterrows(): 
        if row['indicator'] != 0: 
            actions = actions + 1
            post = day_bars.loc[row.name:]
            first = features.max_or_min_first(np.array(post['close']), delta, row['close'])
            if row['indicator'] == 1:
                calls = calls + 1
                if first > row['close']:
                    #print(f'Call correct {row["close"]}/{first} on {index}')
                    c_correct = c_correct + 1
                    correct_bars.append(row)
                else:
                    incorrect_bars.append(row)
            elif row['indicator'] == -1:
                puts = puts + 1
                if first != 0 and first < row['close']:
                    #print(f'Put correct {row["close"]}/{first} on {index}')
                    p_correct = p_correct + 1
                    #correct_bars.append(row)
            
print(f'accuracy {(p_correct+c_correct)/actions}')
print(f'put accuracy {p_correct/puts} actions {puts}')
print(f'call accuracy {c_correct/calls} actions {calls}')

pd.DataFrame(data=correct_bars).to_csv(f'../results/correct_bars.csv', index=True)
pd.DataFrame(data=incorrect_bars).to_csv(f'../results/incorrect_bars.csv', index=True)