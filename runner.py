from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strat import buy_strat, sell_strat, trend_strat
from datetime import datetime, timedelta

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

last_notify = None

while (True):
    notify = False
    if last_notify == None or (datetime.now() - last_notify) >= timedelta(hours=2):
        last_notify = datetime.now()
        notify = True

    clock = trading_client.get_clock()

    if clock.is_open:
        # Check open positions for trend in order to deal with first
        current_positions = trading_client.get_all_positions()
        current_positions = [p.symbol for p in current_positions]
        current_positions_info = trend_strat(current_positions, stock_market_client, datetime.now(), notify)
        sell_strat(current_positions_info, trading_client)

        # Next loop all the symbols we have stored
        symbols = []
        with open('stocks.txt') as file:
            for line in file:
                symbols.append(line.strip())

        stock_trends = trend_strat(symbols, stock_market_client, datetime.now(), notify)
        sell_strat(stock_trends, trading_client)
        buy_strat(stock_trends, trading_client, stock_market_client)

    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))