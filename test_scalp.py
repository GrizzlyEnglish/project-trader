from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import AssetClass
from alpaca.common.exceptions import APIError
from dotenv import load_dotenv
from helpers.load_stocks import load_symbols
from helpers import options, get_data, buy
from datetime import datetime, timedelta
from strats import scalp

import os
load_dotenv()


api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_symbols('scalp_symbols.txt')
enters = scalp.enter(['MSFT'], market_client, datetime(2024, 8, 9, 17, 17))