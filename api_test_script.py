from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.requests import StockLatestQuoteRequest

import pandas as pd

api_key = ''
api_secret = ''

trading_client = TradingClient(api_key, api_secret, paper=True)
broker_client = BrokerClient(api_key, api_secret)
market_client = StockHistoricalDataClient(api_key, api_secret)

positions = trading_client.get_all_positions()

pos = next((x for x in positions if x.symbol == 'FSR'), None)
print(float(pos.unrealized_pl))