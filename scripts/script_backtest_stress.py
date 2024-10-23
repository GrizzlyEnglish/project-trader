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

end = datetime(2024, 10, 22, 12, 30)
start = end - timedelta(days=1)

positions = []
full_actions = 0
full_correct_actions = 0
buy_qty = 5

symbols = ast.literal_eval(os.getenv('SYMBOLS'))

def next_friday(date):
    days_until_friday = (4 - date.weekday() + 7) % 7
    days_until_friday = 7 if days_until_friday == 0 else days_until_friday

    return date + timedelta(days=days_until_friday)

def create_option_symbol(underlying, dte, call_put, strike):
    strike_formatted = f"{strike:08.3f}".replace('.', '').rjust(8, '0')
    date = dte.strftime("%y%m%d")
    option_symbol = f"{underlying}{date}{call_put}{strike_formatted}"
    
    return option_symbol

def backtest_enter(symbol, idx, row, signal, enter, model):
    global actions, correct_actions

    index = idx[1]

    market_open = datetime.combine(index, time(13, 30), timezone.utc)
    market_close = datetime.combine(index, time(19, 1), timezone.utc)

    if index <= market_open or index >= market_close:
        return

    close = row['close']

    strike_price = math.floor(close)

    if enter:
        type = 'P'
        contract_type = 'put'
        if signal == 'Buy':
            type = 'C'
            contract_type = 'call'

        contract_symbol = create_option_symbol(symbol, next_friday(index), type, strike_price)

        bars = options.get_bars(contract_symbol, index - timedelta(hours=1), index, option_client)

        if bars.empty:
            return

        contract_price = bars['close'].iloc[-1]

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
                'cost_basis': contract_price * buy_qty * 100,
                'bought_at': index,
                'qty': buy_qty,
                'date_of': index.date()
            }))

    # check for exits

def backtest_exit(p, exit, reason, close, mv, index, pl, symbol):
    global actions, correct_actions, total

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
            'pl': pl
        }
        actions = actions + 1
        if pl > 0 or mv == 0:
            correct_actions = correct_actions + 1
        total = total + (mv - p.cost_basis)
        positions.remove(p)
        tracker.clear(p.symbol)

accuracies = []
full_total = 0
for i in range(10):
    actions = 0
    correct_actions = 0
    total = 0

    backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions)

    print(f'Accuracy for {i}: {correct_actions/actions}')
    accuracies.append({
        'index': i,
        'correct': correct_actions,
        'actions': actions,
        'acccuracy': correct_actions/actions,
        'pl': total
    })

    full_actions = full_actions + actions
    full_correct_actions = full_correct_actions + correct_actions
    full_total = full_total + total

pd.DataFrame(data=accuracies).to_csv(f'../results/backtest_stress.csv', index=True)