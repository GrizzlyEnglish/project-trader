import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from src.strategies import trending_model
from src.helpers import get_data
from datetime import datetime, timedelta

import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

model = trending_model.TrendingModel('SPY', market_client)
end = datetime(2024, 11, 27, 20)
bars = get_data.get_bars('SPY', end - timedelta(days=30), end, market_client)
model.add_bars(bars)
model.feature_engineer_bars()
model.classify()

model.generate_model()