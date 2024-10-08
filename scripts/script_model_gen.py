import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.strats import short_enter
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from datetime import datetime

import math

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)

model_info = short_enter.generate_short_models(market_client, datetime.now(), '../params.json')