from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime, timedelta
from strats import short_enter
from helpers import features, load_stocks, class_model, short_classifier, overnight_classifier

import os
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

short_info = load_stocks.load_symbol_information('short_option_symbols.txt')
overnight_info = load_stocks.load_symbol_information('overnight_option_symbols.txt')

save = True

acc = []

def save_bars(model_bars, name, symbol):
    b_bars = model_bars[model_bars['label'] == class_model.label_to_int('buy')]
    b_bars.to_csv(f'{symbol}_{name}_buy_signals.csv', index=True)

    s_bars = model_bars[model_bars['label'] == class_model.label_to_int('sell')]
    s_bars.to_csv(f'{symbol}_{name}_sell_signals.csv', index=True)

start = datetime(2024, 9, 15, 12, 30)

'''
for info in short_info:
    symbol = info['symbol']
    day_diff = info['day_diff']
    time_window = info['time_window']
    look_back = info['look_back']
    look_forward = info['look_forward']

    s = start - timedelta(days=day_diff)
    e = start + timedelta(days=1)

    timer_start = datetime.now()
    bars = class_model.get_model_bars(symbol, market_client, s, e, time_window, short_classifier.classification, look_back, look_forward, TimeFrameUnit.Minute)
    model, model_bars, arccuracy, buys, sells = class_model.generate_model(symbol, bars)

    acc.append([symbol, 'short', arccuracy])

    if save:
        save_bars(model_bars, 'short', symbol)

    timer_end = datetime.now()

    print(f'Took {symbol} {timer_end - timer_start}')
'''

for info in overnight_info:
    symbol = info['symbol']
    day_diff = info['day_diff']
    time_window = info['time_window']
    look_back = info['look_back']
    look_forward = info['look_forward']

    s = start - timedelta(days=day_diff)
    e = start + timedelta(days=1)

    timer_start = datetime.now()
    bars = class_model.get_model_bars(symbol, market_client, s, e, time_window, overnight_classifier.classification, look_back, look_forward, TimeFrameUnit.Hour)
    model, model_bars, arccuracy, buys, sells = class_model.generate_model(symbol, bars)

    acc.append([symbol, 'overnight', arccuracy])

    if save:
        save_bars(model_bars, 'overnight', symbol)

    timer_end = datetime.now()

    print(f'Took {symbol} {timer_end - timer_start}')

df = pd.DataFrame(columns=['symbol', 'class', 'accuracy'], data=acc)
df.to_csv(f'test_models.csv', index=True)