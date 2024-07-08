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
from helpers.get_data import get_bars

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

end = datetime.now()
start = datetime.now() - timedelta(days=7)

bars = get_bars('NVDA', start, end, market_client)

cost1 = bars['close'].mean()
vol1 = bars['volume'].mean()

bars = get_bars('LUNR', start, end, market_client)

cost = bars['close'].mean()
vol = bars['volume'].mean()

print(cost)