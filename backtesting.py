from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.trend_logic import weight_symbol_current_status
from helpers.get_data import get_bars
from helpers.features import get_percentage_diff
from strats.entry import get_option_entry, get_stock_entry
from strats.exit import get_exit_symbols, determine_if_exiting
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbols

import os
import pandas as pd
import numpy as np

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

indexes = [[], []] 
data = []

year = 2022
start = datetime(year, 1, 1, 12, 30)
holding = {}

assets = [
    'AVGO', 'NVDA', 'AAPL', 'GEO', 'GAP', 'BB', 'NOK', 'SPY', 'QQQ', 'HIMS'
]

while (start.year == 2022):
    if start.weekday() <= 5:
        start_format = datetime.strftime(start, "%m/%d/%Y")

        # Get weights
        weighted_assets = weight_symbol_current_status(assets, market_client, start)

        #Stocks
        ## Get exits and see if "holding" and add exit price
        exit_stock = get_exit_symbols(weighted_assets)

        keys_to_remove = []

        for s in holding:
            keys = holding[s]
            current_trend = next((es for es in exit_stock if es['symbol'] == s), None)

            # Marked as an exit see if we actually want to
            if current_trend != None:
                status = determine_if_exiting(s, current_trend, 0, 0)
                if status['sell']:
                    days_diff = 1
                    if start.weekday() == 5:
                        days_diff = 3
                    bars = get_bars(s, start, start + timedelta(days=days_diff), market_client)
                    if not bars.empty:
                        for k in keys:
                            # We do pretend we exited and get some data
                            data[k]['exit_price'] = bars.iloc[0]['close']
                            data[k]['predicted_next_close'] = status['predicted_close']
                            data[k]['actual_next_close'] = bars.iloc[-1]['close'] 
                            data[k]['prediction_var'] = get_percentage_diff(bars.iloc[-1]['close'], status['predicted_close'])
                            pl = data[k]['enter_price'] - data[k]['exit_price']
                            data[k]['p/l'] = pl
                            if pl > 0:
                                data[k]['g/b'] = 1
                            else:
                                data[k]['g/b'] = 0
                        # Remove from stuff we are holding
                        keys_to_remove.append(s)

        for key in keys_to_remove:
            holding.pop(key, None)

        ## Get entries and add to entry 
        enter_stock = get_stock_entry(weighted_assets)

        for s in enter_stock:
            symbol = s['symbol'] 
            indexes[0].append(start_format)
            indexes[1].append(symbol)
            # Get some data
            data.append({
                'enter_price': s['last_close'], 
                'exit_price': 0, 
                'predicted_next_close': 0, 
                'actual_next_close': 0
                })
            key = len(data) - 1
            # Add it to holding to be able to "sell" later
            if symbol not in holding:
                holding[symbol] = []
            holding[symbol].append(key)

    start = start + timedelta(days=1)

df = pd.DataFrame(data, index=indexes)
df.to_csv('backtest.csv', index=True)