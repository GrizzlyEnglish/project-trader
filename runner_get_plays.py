from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.trend_logic import weight_symbol_current_status
from strats.entry import enter, get_entry_symbols, enter_option
from strats.exit import get_exit_symbols, exit
from datetime import datetime, timedelta
from helpers.load_stocks import load_symbols

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_symbols()

start = datetime.now()

weighted_assets = weight_symbol_current_status(assets, market_client, start)

option = enter_option(weighted_assets, trading_client, market_client, False)
print(option)