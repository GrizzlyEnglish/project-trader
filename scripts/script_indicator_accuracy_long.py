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
import ast

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

symbols = ast.literal_eval(os.getenv('LONG_SYMBOLS'))

for symbol in symbols:
    delta = 1 
    end = datetime(2024, 11, 29, 19)
    start = end - timedelta(days=90)
    bars_handlers = bars_data.BarData(symbol, start, end, market_client)
    df = bars_handlers.get_bars(1, 'Hour')

    df['indicator'] = df.apply(features.vortext_indicator_long, axis=1)

    actions = 0
    p_correct = 0
    c_correct = 0
    calls = 0
    puts = 0
    incorrect_bars = []
    correct_bars = []
    dates = np.unique(df.index.get_level_values('timestamp').date)

    for index, row in df.iterrows(): 
        if row['indicator'] != 0: 
            actions = actions + 1
            post = df.loc[row.name:]
            first = features.max_or_min_first(np.array(post['close']), delta, row['close'])
            if row['indicator'] == 1:
                calls = calls + 1
                if first > row['close']:
                    c_correct = c_correct + 1
                    correct_bars.append(row)
                else:
                    incorrect_bars.append(row)
            elif row['indicator'] == -1:
                puts = puts + 1
                if first != 0 and first < row['close']:
                    p_correct = p_correct + 1
                
    print(f'{symbol}')
    if actions > 0:
        print(f'accuracy {(p_correct+c_correct)/actions}')
    if puts > 0:
        print(f'put accuracy {p_correct/puts} actions {puts}')
    if calls > 0:
        print(f'call accuracy {c_correct/calls} actions {calls}')

    pd.DataFrame(data=correct_bars).to_csv(f'../results/correct_bars.csv', index=True)
    pd.DataFrame(data=incorrect_bars).to_csv(f'../results/incorrect_bars.csv', index=True)