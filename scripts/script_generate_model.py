import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from src.strategies import trending_model
from src.helpers import get_data
from datetime import datetime

import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

bars = get_data.get_bars('SPY', datetime(2024, 10, 21, 9, 30), datetime(2024, 11, 19, 20), market_client)
bars1 = get_data.get_bars('QQQ', datetime(2024, 10, 21, 9, 30), datetime(2024, 11, 19, 20), market_client)
bars2 = get_data.get_bars('PLTR', datetime(2024, 10, 21, 9, 30), datetime(2024, 11, 19, 20), market_client)
bars3 = get_data.get_bars('NVDA', datetime(2024, 10, 21, 9, 30), datetime(2024, 11, 19, 20), market_client)

bars = pd.concat([bars, bars1, bars2, bars3], ignore_index=False)

model = trending_model.TrendingModel('SPY', market_client)
model.add_bars(bars)
model.feature_engineer_bars()
model.classify()

model.generate_model()