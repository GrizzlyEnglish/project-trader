from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange
from dotenv import load_dotenv
from strat import buy_strat, sell_strat, info_strat
from discord import SyncWebhook
from datetime import datetime,timedelta

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
stock_discord_url = os.getenv('TEST_DISCORD_URL')
crypto_discord_url = os.getenv('TEST_DISCORD_URL')
alpaca_discord_url = os.getenv('TEST_DISCORD_URL')

trading_client = TradingClient(api_key, api_secret, paper=paper)
crypto_market_client = CryptoHistoricalDataClient(api_key, api_secret)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

discord_stock = SyncWebhook.from_url(stock_discord_url)
discord_crypto = SyncWebhook.from_url(crypto_discord_url)
discord_alpaca = SyncWebhook.from_url(alpaca_discord_url)

#stock_info = info_strat("Stock", ["VLO"], stock_market_client, discord_stock, datetime.now() - timedelta(hours=7))

class FakeStock:
    def __init__(self):
        self.symbol = "SHIB/USD"
        self.trend = 42

sell_strat('Crypto', [FakeStock()], trading_client, discord_alpaca)