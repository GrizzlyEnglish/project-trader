from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import OrderSide, AssetClass
from dotenv import load_dotenv
from discord import SyncWebhook
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import timedelta, datetime
from helpers.options import get_option_call, get_option_put

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

#options = get_option_put('AAPL', 210, 190, trading_client)
#print(options)

current_positions = trading_client.get_all_positions()

for position in current_positions:
    if position.asset_class == AssetClass.US_OPTION:
        contract = trading_client.get_option_contract(position.symbol)
        print(contract)