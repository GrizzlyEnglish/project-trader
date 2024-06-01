from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from strat import buy_strat, sell_strat, trend_strat
from discord_webhook import DiscordWebhook
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

def stock_runner(notify):
    clock = trading_client.get_clock()

    if clock.is_open:
        stocks = []
        with open('stocks.txt') as file:
            for line in file:
                stocks.append(line.strip())  

        stock_info = trend_strat(stocks, stock_market_client, datetime.now(), notify)

        sell_strat(stock_info['sell'], stock_info['buy'], trading_client)

        buy_strat(stock_info['buy'], trading_client, stock_market_client)

last_notify = None

while (True):
    notify = False
    if last_notify == None or (datetime.now() - last_notify) >= timedelta(hours=2):
        last_notify = datetime.now()
        notify = True

    stock_runner(False)
    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))