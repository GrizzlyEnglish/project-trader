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

positions = trading_client.get_all_positions()
positions = [{'symbol': p.symbol, 'qty': p.qty_available} for p in positions]

print(any(p['symbol'] == 'SPY' for p in positions))