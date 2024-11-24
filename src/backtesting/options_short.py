import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, time, timezone, timedelta

from src.backtesting import short, chart
from src.backtesting.short import backtest
from src.helpers import options, features, tracker
from src.strats.short import do_exit

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import ast

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

close_series = {}
purchased_series = {}
sell_series = {}
pl_series = []
telemetry = []
positions = []
actions = 0
correct_actions = 0
total = {}
buy_qty = int(os.getenv('BUY_AMOUNT'))

symbols = ast.literal_eval(os.getenv('SYMBOLS'))

def run_option_backtest(start, end, show_graph):
    global pl_series, correct_actions, actions, total, telemetry

    for s in symbols:
        close_series[s] = []
        purchased_series[s] = []
        sell_series[s] = []
        total[s] = 0

    def backtest_enter(symbol, idx, row, signal, enter, model):
        global actions, correct_actions

        index = idx[1]

        market_open = datetime.combine(index, time(13, 30), timezone.utc)
        market_close = datetime.combine(index, time(19, 1), timezone.utc)

        if index <= market_open or index >= market_close:
            return

        close = row['close']
        close_series[symbol].append([index, close])

        strike_price = math.floor(close)

        if enter:
            type = 'P'
            contract_type = 'put'
            if signal == 'Buy':
                type = 'C'
                contract_type = 'call'

            contract_symbol = options.create_option_symbol(symbol, index if symbol == 'QQQ' or symbol == 'SPY' else options.next_friday(index) , type, strike_price)

            bars = options.get_bars(contract_symbol, index - timedelta(hours=1), index, option_client)

            if bars.empty:
                print(f'No bars for {contract_symbol}')
                return

            contract_price = bars['close'].iloc[-1] * buy_qty

            if contract_price > 0:
                class DotAccessibleDict:
                    def __init__(self, **entries):
                        self.__dict__.update(entries)
                positions.append(DotAccessibleDict(**{
                    'symbol': contract_symbol,
                    'contract_type': contract_type,
                    'strike_price': strike_price,
                    'close': close,
                    'price': contract_price,
                    'cost_basis': contract_price * 100,
                    'bought_at': index,
                    'qty': buy_qty,
                    'market_value': contract_price * 100,
                    'unrealized_plpc': 0,
                    'date_of': index.date()
                }))
                print(f'Purchased {contract_symbol} at {index}')
                purchased_series[symbol].append(index)

        # check for exits

    def backtest_exit(p, exit, reason, close, mv, index, pl, symbol):
        global actions, telemetry, pl_series, sell_series, correct_actions, total

        if exit:
            print(f'Sold {symbol} for {reason}')
            tel = {
                'symbol': symbol,
                'contract': p.symbol,
                'strike_price': p.strike_price,
                'sold_close': close,
                'bought_close': p.close,
                'type': p.contract_type,
                'bought_price': p.cost_basis,
                'sold_price': mv,
                'bought_at': p.bought_at,
                'sold_at': index,
                'held_for': index - p.bought_at,
                'sold_for': reason,
                'pl': (mv - p.cost_basis)
            }
            sell_series[symbol].append(index)
            telemetry.append(tel)
            pl_series.append([tel['type'], (tel['sold_price'] - tel['bought_price'])])
            actions = actions + 1
            if pl > 0 or mv == 0:
                correct_actions = correct_actions + 1
            total[symbol] = total[symbol] + (mv - p.cost_basis)
            positions.remove(p)
            tracker.clear(p.symbol)

    backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions)

    full_total = 0
    for cs in symbols:
        full_total = full_total + total[cs]
        print(f'{cs} total {total[cs]}')

    accuracy = 0
    if actions > 0:
        accuracy = correct_actions/actions
        print(f'Accuracy {accuracy} total {full_total}')
    
    if len(positions) > 0:
        for p in positions:
            print(f'Still holding {p.symbol} with pl {p.unrealized_plpc}')

    pd.DataFrame(data=telemetry).to_csv(f'../results/short_backtest.csv', index=True)

    if show_graph:
        fig = plt.figure(1)

        pl_series = np.array(pl_series)
        x = [float(p) for p in pl_series[:, 1]]
        y = pl_series[:, 0]
        categories = [f'{y[i]} {i+1}' for i in range(len(y))]

        plt.bar(categories, x, color=['orange' if 'call' in value else 'purple' for value in y])

        plt.xlabel('Option type')
        plt.ylabel('P/L')
        plt.title('Option backtest p/l')

        # Show the plot
        plt.show()

    return accuracy, full_total, total