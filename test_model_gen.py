from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from helpers.get_data import get_bars
from datetime import timedelta, datetime
from strat import fully_generate_all_stocks

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
stock_discord_url = os.getenv('STOCK_DISCORD_URL')
alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')

days = float(os.getenv('FULL_DAY_COUNT'))
start = datetime.now()
count = 0

trading_client = TradingClient(api_key, api_secret, paper=paper)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

stocks =[]

fully_generate_all_stocks(trading_client, stock_market_client, datetime.now())