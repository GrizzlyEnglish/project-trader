import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.helpers import load_parameters, class_model
from src.classifiers import overnight
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

market_client = StockHistoricalDataClient(api_key, api_secret)

params = load_parameters.load_symbol_parameters('../params.json')

models = []

for p in params:
    symbol = p['symbol']
    print('OVERNIGHT Gen')
    overnight_model_info = class_model.generate_model(symbol, p['overnight'], market_client, overnight.classification, datetime.now())