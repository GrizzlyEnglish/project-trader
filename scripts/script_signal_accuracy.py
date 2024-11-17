import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import short
from src.helpers import get_data

import ast
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

end = datetime(2024, 11, 15, 12, 30)
start = end - timedelta(days=1)

symbols = ast.literal_eval(os.getenv('SYMBOLS'))

signals = {}

for s in symbols:
    signals[s] = []

def exit():
    return

def enter(symbol, idx, row, signal, enter, model):
    if signal == 'Hold':
        return

    delta = float(os.getenv(f'{symbol}_DELTA'))
    trend = int(os.getenv(f'{symbol}_TREND'))

    dt = idx[1]

    bars = get_data.get_bars(symbol, dt, dt + timedelta(minutes=trend), market_client, 1, 'Min')

    call = delta
    put = -delta

    max_idx = bars['close'].idxmax()
    min_idx = bars['close'].idxmin()

    max = bars.loc[max_idx]['close']
    min = bars.loc[min_idx]['close']

    correct = False

    max_d = max - row["close"]
    min_d = min - row["close"]

    if signal == 'Buy':
        correct = (min_d >= put or max_idx < min_idx) and max >= call
    elif signal == 'Sell':
        correct = (max_d <= call or min_idx < max_idx) and min <= put

    signals[symbol].append({'signal': signal, 'close': row["close"], 'max': max, 'min': min, 'max_diff': max_d, 'min_diff': min_d, 'max_idx': max_idx, 'min_idx': min_idx, 'correct': correct})

short.backtest(start, end, enter, exit , market_client, option_client, [])

for cs in symbols:
    df = pd.DataFrame(signals[cs])
    df.to_csv(f'../results/{cs}_signal_acc.csv', index=True)
    print(df)
    correct = df['correct'].sum()
    print(f'{correct/len(df)}')