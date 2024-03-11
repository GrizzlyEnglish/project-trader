from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.requests import StockLatestQuoteRequest

from nn.generate_model import generate_model

import pandas as pd

api_key = ''
api_secret = ''

market_client = StockHistoricalDataClient(api_key, api_secret)

generate_model('HOOK', market_client)