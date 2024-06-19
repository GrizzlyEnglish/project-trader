from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.trend_logic import weight_symbol_current_status
from strats.entry import enter, get_stock_entry 
from strats.exit import get_exit_symbols, exit
from datetime import datetime, timedelta
from messaging.discord import send_stock_info_messages
from helpers.load_stocks import load_symbols

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

last_notify = None

# 1. Get symbols
assets = load_symbols()

while (True):
    start = datetime.now()

    # get the weight of the assets
    weighted_assets = weight_symbol_current_status(assets, market_client, start)

    if last_notify == None or (datetime.now() - last_notify) >= timedelta(hours=1):
        # notify top 10 enter/exits
        last_notify = datetime.now()
        enter_assets = get_stock_entry(weighted_assets)
        exit_assets = get_exit_symbols(weighted_assets) 
        send_stock_info_messages(enter_assets, exit_assets)

    # 2. Exit any open positions we need to
    exit(weighted_assets, trading_client, market_client)

    # 3. Enter with any buying power we have
    enter(weighted_assets, trading_client, market_client)