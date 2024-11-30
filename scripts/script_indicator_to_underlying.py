import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import get_data, features, chart

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

end = datetime(2024, 7, 9, 20)
start = end - timedelta(days=day_diff)

for symbol in symbols:
    close_prices[symbol] = []
    call_signal[symbol] = []
    hold_signal[symbol] = []
    put_signal[symbol] = []

    bars = get_data.get_bars(symbol, start, end, market_client, 1, 'Min')
    bars = features.feature_engineer_df(bars)
    bars['indicator'] = bars.apply(features.my_indicator, axis=1)

    calls = bars[bars['indicator'] == 1]
    puts = bars[bars['indicator'] == -1]

    print(f'overall calls: {len(calls)} puts: {len(puts)}')

    dtstr = end.strftime("%Y-%m-%d")
    day_bars = bars.loc[(symbol, dtstr)]

    calls = day_bars[day_bars['indicator'] == 1]
    puts = day_bars[day_bars['indicator'] == -1]

    print(f'day calls: {len(calls)} puts: {len(puts)}')

    for index, row in day_bars.iterrows():
        spot = len(close_prices[symbol]) + 1
        close_prices[symbol].append([index, row['close']])
        if row['indicator'] == 1:
            call_signal[symbol].append(index)
        elif row['indicator'] == -1:
            put_signal[symbol].append(index)
        else:
            hold_signal[symbol].append(index)

for cs in symbols:
    print(f'{cs}: Call signal:{len(call_signal[cs])} Put signal:{len(put_signal[cs])} Hold signal: {len(hold_signal[cs])}')
    close_series = np.array(close_prices[cs])
    chart.chart_with_signals(close_series, call_signal[cs], put_signal[cs], f'Classification for {cs} on {end}', 'Time', 'Stock price', fig)
    fig = fig + 1

# Show the plot
plt.show()