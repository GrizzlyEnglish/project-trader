from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import AssetClass
from dotenv import load_dotenv
from helpers.load_stocks import load_symbols
from datetime import datetime
from strats import classification

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_symbols('option_symbols.txt')
classified_time = None

time_window = float(os.getenv('TIME_WINDOW'))
time_diff = time_window * 60

while (True):
    clock = trading_client.get_clock()

    if clock.is_open:
        classifications = []

        if (classified_time == None or time.time() - classified_time >= time_diff) and datetime.now().hour > 9:
            classifications = classification.classify_symbols(assets, market_client, datetime.now())
            classified_time = time.time() 

        current_positions = trading_client.get_all_positions()
        positions = [p for p in current_positions if p.asset_class == AssetClass.US_OPTION]

        for c in classifications:
            classification.enter(c, positions, trading_client, market_client)

        for p in positions:
            classification.exit(p, classifications, trading_client)

    time.sleep(60)