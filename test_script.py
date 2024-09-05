from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from strats import short_classification
from helpers.load_stocks import load_symbols
from helpers.short_classifier import label_to_int

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_symbols('option_symbols.txt')
#assets = ['SPY', 'QQQ', 'NVDA', 'META']
#assets = ['SPY']
save = False 

day_span = int(os.getenv('SHORT_CLASS_DAY_SPAN'))
start = datetime(2024, 8, 29, 12, 30)
s = start - timedelta(days=day_span)
e = start + timedelta(days=1)
time_window = int(os.getenv('TIME_WINDOW'))

for symbol in assets:
    bars = short_classification.get_model_bars(symbol, market_client, s, e, time_window)
    model, model_bars = short_classification.generate_model(symbol, bars)

    if save:
        b_bars = model_bars[model_bars['label'] == label_to_int('buy')]
        b_bars.to_csv(f'{symbol}_buy_signals.csv', index=True)

        s_bars = model_bars[model_bars['label'] == label_to_int('sell')]
        s_bars.to_csv(f'{symbol}_sell_signals.csv', index=True)

        #model_bars.to_csv(f'{symbol}_bars.csv', index=True)

    print()