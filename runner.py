from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from src.strats import overnight_enter, short_enter, exit
from src.helpers import load_stocks, get_data
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient

import schedule
import time
import os

short_symbol_info = load_stocks.load_symbol_information('short_option_symbols.txt')
overnight_symbol_info = load_stocks.load_symbol_information('overnight_option_symbols.txt')

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

# Helpers
def is_within_open_market(offset=False):
    now = datetime.now()
    start_hour = 9
    if offset:
        start_hour = 10
    start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=0, second=0, microsecond=0)
    return start_time <= now <= end_time

# Tasks
def check_overnight_enter():
    print("Checking for entry to overnight positions")
    info = [i for i in overnight_symbol_info if i['symbol'] == 'SPY' or 'QQQ']
    overnight_enter.enter_overnight(info, market_client, trading_client, option_client)

def dont_hold_overnight():
    print("Close all currently open positions, so we dont hold overnight")
    positions = get_data.get_positions(trading_client)
    for p in positions:
        trading_client.close_position(p.symbol)

def check_short_enter():
    print("Checking for entry to short positions")
    try:
        short_enter.enter_short(short_symbol_info, market_client, trading_client, option_client)
    except Exception as e:
        print(e)

def check_exit():
    print("Checking for exits")
    exit.exit(trading_client, option_client)

def run_threaded(job_func, *args):
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.submit(job_func, *args)

schedule.every().day.at("15:00").do(dont_hold_overnight)
schedule.every().day.at("15:30").do(check_overnight_enter)

schedule.every(3).minutes.do(lambda: run_threaded(check_short_enter) if is_within_open_market(True) else None)
schedule.every(30).seconds.do(lambda: run_threaded(check_exit) if is_within_open_market() else None)

# Immediately run these
if is_within_open_market():
    check_exit()
if is_within_open_market(True):
    check_short_enter()

# Schedule after
while True:
    schedule.run_pending()
    time.sleep(1)