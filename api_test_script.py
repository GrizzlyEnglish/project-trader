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

#trend_strat(['AAPL'], stock_market_client, datetime(2024, 5, 25, 11), True, False, False)
previous_date = datetime.now() - timedelta(days=10, hours=1)
print(previous_date)
orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=OrderSide.BUY, symbols=['BRFS'])) 
print(orders)