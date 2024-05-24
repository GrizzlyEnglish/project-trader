from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from discord import SyncWebhook
from datetime import timedelta, datetime

from helpers.trend_logic import predict_ewm
from strat import info_strat, sell_strat

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

discord_stock = SyncWebhook.from_url(stock_discord_url)
discord_crypto = SyncWebhook.from_url(crypto_discord_url)
discord_alpaca = SyncWebhook.from_url(alpaca_discord_url)

predict_ewm('EQH', datetime.now(), stock_market_client, True)
#info_strat(['AAPL'], stock_market_client, discord_stock, datetime.now(), True)
#sell_strat('Stock', [{'symbol': 'DXYZ'}], [], trading_client, discord_alpaca)