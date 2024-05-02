from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
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
crypto_discord_url = os.getenv('CRYPTO_DISCORD_URL')
alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')

trading_client = TradingClient(api_key, api_secret, paper=paper)
crypto_market_client = CryptoHistoricalDataClient(api_key, api_secret)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

discord_stock = SyncWebhook.from_url(stock_discord_url)
discord_crypto = SyncWebhook.from_url(crypto_discord_url)
discord_alpaca = SyncWebhook.from_url(alpaca_discord_url)


def stock_runner(notify):
    clock = trading_client.get_clock()

    if clock.is_open:
        stocks = []
        with open('stocks.txt') as file:
            for line in file:
                stocks.append(line.strip())  
        stock_info = info_strat(stocks, stock_market_client, discord_stock, datetime.now(), notify)

        if len(stock_info['sell']) > 0:
            sell_strat('Stock', stock_info['sell'], trading_client, discord_alpaca)

        if len(stock_info['buy']) > 0:
            buy_strat(stock_info['buy'], trading_client, stock_market_client, discord_alpaca)

def crypto_runner(notify):
    request = GetAssetsRequest(asset_class=AssetClass.CRYPTO)
    response = trading_client.get_all_assets(request)
    coins = [c.symbol for c in response if '/USD' in c.symbol if filter_strat(c.symbol, crypto_market_client, datetime.now())]
    coin_info = info_strat(coins, crypto_market_client, discord_crypto, datetime.now(), notify)

    if len(coin_info['sell']) > 0:
        sell_strat('Crypto', coin_info['sell'], trading_client, discord_alpaca)

    if len(coin_info['buy']) > 0:
        buy_strat(coin_info['buy'], trading_client, crypto_market_client, discord_crypto)

last_notify = None

while (True):
    notify = False
    if last_notify == None or (datetime.now() - last_notify) >= timedelta(hours=3):
        last_notify = datetime.now()
        notify = True

    stock_runner(notify)
    crypto_runner(notify)
    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))