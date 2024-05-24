from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange
from dotenv import load_dotenv
from strat import buy_strat, sell_strat, info_strat, filter_strat
from discord import SyncWebhook
from datetime import datetime, timedelta

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
stock_discord_url = os.getenv('STOCK_DISCORD_URL')
alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

discord_stock = SyncWebhook.from_url(stock_discord_url)
discord_alpaca = SyncWebhook.from_url(alpaca_discord_url)


def stock_runner(notify):
    clock = trading_client.get_clock()

    if clock.is_open:
        stocks = []
        with open('stocks.txt') as file:
            for line in file:
                stocks.append(line.strip())  
        stock_info = info_strat(stocks, stock_market_client, discord_stock, datetime.now(), notify)

        sell_strat(stock_info['sell'], stock_info['buy'], trading_client, discord_alpaca)

        buy_strat(stock_info['buy'], trading_client, stock_market_client, discord_alpaca)

last_notify = None

while (True):
    notify = False
    if last_notify == None or (datetime.now() - last_notify) >= timedelta(hours=3):
        last_notify = datetime.now()
        notify = True

    stock_runner(notify)
    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))