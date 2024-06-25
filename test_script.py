from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import OrderSide, AssetClass
from dotenv import load_dotenv
from discord import SyncWebhook
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import timedelta, datetime
from helpers.options import get_option_call, get_option_put
from helpers.get_data import check_exit_pdt_gaurd

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

print(check_exit_pdt_gaurd('VALE', trading_client))