from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange
from dotenv import load_dotenv
from strat import buy_strat, sell_strat, info_strat
from discord import SyncWebhook
from datetime import datetime

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

while (True):
    clock = trading_client.get_clock()

    stock_info = { 'buy': [], 'sell': []}
    coin_info = { 'buy': [], 'sell': []}

    if clock.is_open:
        request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE, exchange=AssetExchange.NYSE)
        response = trading_client.get_all_assets(request)
        stocks = [s.symbol for s in response]
        stock_info = info_strat("Stocks", stocks, stock_market_client, discord_stock, datetime.now())

    # Crypto always open
    request = GetAssetsRequest(asset_class=AssetClass.CRYPTO)
    response = trading_client.get_all_assets(request)
    coins = [c.symbol for c in response if '/USD' in c.symbol]
    coin_info = info_strat("Crypto", coins, crypto_market_client, discord_crypto, datetime.now())

    if len(stock_info['sell']) > 0:
        sell_strat(stock_info['sell'], trading_client, discord_alpaca)

    if len(coin_info['sell']) > 0:
        sell_strat(coin_info['sell'], trading_client, discord_alpaca)

    if len(stock_info['buy']) > 0:
        buy_strat(coin_info['buy'], trading_client, crypto_market_client, discord_crypto)

    if len(coin_info['buy']) > 0:
        buy_strat(stock_info['buy'], trading_client, stock_market_client, discord_stock)

    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))