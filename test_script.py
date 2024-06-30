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
from helpers.trend_logic import predict_status 

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

predicted = predict_status('QQQ', market_client, datetime(2024, 6, 28, 13))
print(predicted)

#predicted = get_predicted_price('CHWY', market_client)
#print(predicted)