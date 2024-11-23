import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import get_data, features
from src.classifiers import trending
from src.backtesting import chart

import numpy as np
import ast
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

close_prices = {}

call_signal = {}
put_signal = {}
hold_signal = {}
fig = 1

symbols = ast.literal_eval(os.getenv('SYMBOLS'))
day_diff = int(os.getenv('DAYDIFF'))

end = datetime(2024, 11, 14, 20)
start = end - timedelta(days=day_diff)

for symbol in symbols:
    close_prices[symbol] = []
    call_signal[symbol] = []
    hold_signal[symbol] = []
    put_signal[symbol] = []

    bars = get_data.get_bars(symbol, start, end, market_client, 1, 'Min')
    bars = features.feature_engineer_df(bars)
    bars = trending.classification(bars)

    calls = bars[bars['label'] == 'buy']
    puts = bars[bars['label'] == 'sell']

    print(f'overall calls: {len(calls)} puts: {len(puts)}')

    dtstr = end.strftime("%Y-%m-%d")
    day_bars = bars.loc[(symbol, dtstr)]

    calls = day_bars[day_bars['label'] == 'buy']
    puts = day_bars[day_bars['label'] == 'sell']

    print(f'day calls: {len(calls)} puts: {len(puts)}')

    for index, row in day_bars.iterrows():
        spot = len(close_prices[symbol]) + 1
        close_prices[symbol].append([spot, row['close']])
        if row['label'] == 'buy':
            call_signal[symbol].append(spot)
        elif row['label'] == 'sell':
            put_signal[symbol].append(spot)
        else:
            hold_signal[symbol].append(spot)

for cs in symbols:
    print(f'{cs}: Call signal:{len(call_signal[cs])} Put signal:{len(put_signal[cs])} Hold signal: {len(hold_signal[cs])}')
    close_series = np.array(close_prices[cs])
    chart.chart_with_signals(close_series, call_signal[cs], put_signal[cs], f'Classification for {cs} on {end}', 'Time', 'Stock price', fig)
    fig = fig + 1

# Show the plot
plt.show()