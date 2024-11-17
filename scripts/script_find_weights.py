import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import options_short

import pandas as pd
import ast

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

accuracies = {
    'risk': [],
    'delta': [],
    'accuracy': [],
    'total': []
}

for cs in symbols:
    accuracies[f'total_{cs}'] = []

for j in range(10):
    delta = .4 + (j * .1)
    os.environ['DELTA'] = f'{delta}'

    for i in range(5):
        risk = i+(5*i)
        print(f'RISK={risk} DELTA={delta}')
        os.environ['RISK'] = f'{risk}'
        acc, full_total, totals = options_short.run_option_backtest(start, end, False)
        accuracies['risk'].append(risk)
        accuracies['delta'].append(delta)
        accuracies['accuracy'].append(acc)
        accuracies['total'].append(full_total)
        for cs in symbols:
            amt = totals[cs]
            accuracies[f'total_{cs}'].append(amt)

df = pd.DataFrame(accuracies)
print(df)
