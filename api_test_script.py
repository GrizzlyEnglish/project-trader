from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import OrderSide
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

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

trend = trend_strat(['VLD'], stock_market_client, datetime(2024, 6, 4, 1), True, False, False)
print(trend)