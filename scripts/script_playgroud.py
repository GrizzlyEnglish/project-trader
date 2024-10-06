import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.helpers import load_parameters, class_model, get_data
from src.classifiers import overnight
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit
from dotenv import load_dotenv
from datetime import datetime

import os
import numpy as np
from scipy.optimize import newton

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)

bars = get_data.get_bars('SPY', datetime(2023, 10, 6), datetime(2024, 10, 6), market_client, 1, TimeFrameUnit.Day)

bars['returns'] = bars['close'].pct_change()

daily_volatility = bars['returns'].std()
annual_volatility = daily_volatility * np.sqrt(252)

print(annual_volatility)