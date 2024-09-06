from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from alpaca.trading.requests import StopLimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce, OrderClass
from helpers import buy

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

buy.submit_order('SPY240909P00546000', 1, 4, trading_client)