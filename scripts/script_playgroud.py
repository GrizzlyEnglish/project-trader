import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.helpers import load_parameters, class_model, get_data
from src.classifiers import close 
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

p = {
    'day_diff': 365,
    'time_window': 1,
    'look_back': 5,
    'look_forward': 1,
    'time_unit': 'Hour'
}

close_model_info = class_model.generate_model('SPY', p, market_client, close.classification, datetime.now())