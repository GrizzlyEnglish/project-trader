from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from discord import SyncWebhook
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import timedelta, datetime

from strat import trend_strat

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
stock_discord_url = os.getenv('TEST_DISCORD_URL')
crypto_discord_url = os.getenv('TEST_DISCORD_URL')
alpaca_discord_url = os.getenv('TEST_DISCORD_URL')

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

discord_stock = DiscordWebhook(stock_discord_url)
discord_crypto = DiscordWebhook(crypto_discord_url)
discord_alpaca = DiscordWebhook(alpaca_discord_url)

trend_strat(['AAPL'], stock_market_client, discord_stock, datetime(2024, 5, 25, 11), True, False, False)