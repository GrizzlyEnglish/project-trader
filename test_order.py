from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from alpaca.trading.requests import StopLimitOrderRequest, StopLossRequest, TakeProfitRequest
from alpaca.trading.enums import OrderSide, OrderType, TimeInForce, OrderClass

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

current_positions = trading_client.get_all_positions()

position = current_positions[0]

price = float(position.current_price)
qty = float(position.qty)
contract = position.symbol

stop_loss_order = StopLimitOrderRequest(
    symbol=contract,
    qty=qty, 
    side=OrderSide.SELL,
    type=OrderType.STOP,
    time_in_force=TimeInForce.DAY,
    stop_price=price-0.05,
    limit_price=price-0.10,
    order_type=OrderType.STOP_LIMIT
)
trading_client.submit_order(stop_loss_order)