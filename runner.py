from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from src.data import bars_data, options_data
from src.options import buy, sell
from src.strategies import short_option, long_option
from src.helpers import options
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient

import schedule
import time
import os
import ast
import pytz

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
day_diff = int(os.getenv('DAYDIFF'))
shorts = ast.literal_eval(os.getenv('SHORT_SYMBOLS'))
longs = ast.literal_eval(os.getenv('LONG_SYMBOLS'))

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

last_checked = {}

short_strat = short_option.ShortOption()
long_strat = long_option.LongOption()
buyer = buy.Buy(trading_client, option_client) 
seller = sell.Sell(trading_client, option_client)

# Helpers
def is_within_open_market(offset=False):
    now = datetime.now()
    start_hour = 9
    if offset:
        start_hour = 10
    start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return start_time <= now <= end_time

def dont_hold_overnight():
    print("Close all currently open positions, so we dont hold overnight")
    current_positions = trading_client.get_all_positions()
    for position in current_positions:
        seller.exit(position, 'dont hold overnight')

def check_short_enter():
    print("Checking for entry to short positions")
    for symbol in shorts:
        data = bars_data.BarData(symbol, datetime.now(pytz.UTC) - timedelta(days=day_diff), datetime.now(pytz.UTC) + timedelta(minutes=1), market_client)
        bars = data.get_bars()
        bars = short_strat.enter(bars)
        if not bars.empty:
            #TODO: Scale qty
            b = bars.iloc[-1]
            check_buy(symbol, b)

def check_buy(symbol, b):
    if symbol not in last_checked or last_checked[symbol] != b.index[1]:
        print(f'Checking {symbol} at {b.name[1]} signal {b["signal"]}')
        if b['signal'] != 'hold':
            buyer.purchase(symbol, b['signal'], b['close'], 1)
    else:
        print(f'Already checked {b.index[1]} for {symbol}')

    last_checked[symbol] = b.index[1]

def check_long_enter():
    print("Checking for entry to long positions")
    for symbol in longs:
        data = bars_data.BarData(symbol, datetime.now(pytz.UTC) - timedelta(days=day_diff), datetime.now(pytz.UTC) + timedelta(minutes=1), market_client)
        bars = data.get_bars(1, 'Hour')
        bars = long_strat.enter(bars)
        if not bars.empty:
            #TODO: Scale qty
            b = bars.iloc[-1]
            check_buy(symbol, b)

def check_exit():
    print("Checking for exits")
    current_positions = trading_client.get_all_positions()
    d = options_data.OptionData('', datetime.now(), 'c', 1, option_client)
    for position in current_positions:
        underyling = options.get_underlying_symbol(position.symbol)
        d.set_symbol(position.symbol)
        bars = d.get_bars(datetime.now() - timedelta(days=30), datetime.now())
        if underyling in shorts:
            exit, reason = short_strat.exit(position, bars.iloc[-1])
        else:
            exit, reason = long_strat.exit(position, bars.iloc[-1])
        if exit:
            seller.exit(position, reason)

def run_threaded(job_func, *args):
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(job_func, *args)

schedule.every().day.at("15:00").do(dont_hold_overnight)

schedule.every(30).seconds.do(lambda: run_threaded(check_short_enter) if is_within_open_market() else None)
schedule.every(30).minutes.do(lambda: run_threaded(check_long_enter) if is_within_open_market() else None)
schedule.every(30).seconds.do(lambda: run_threaded(check_exit) if is_within_open_market() else None)

# Immediately run these
if is_within_open_market():
    check_exit()
    check_short_enter()
    check_long_enter()

# Schedule after
while True:
    schedule.run_pending()
    time.sleep(1)