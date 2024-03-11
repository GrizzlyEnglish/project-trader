from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from penny_stock_strat import penny_stock_strat

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
broker_client = BrokerClient(api_key, api_secret)
market_client = StockHistoricalDataClient(api_key, api_secret)

stocks = ['FSR', 'NKLA', 'BKKT', 'OPK', 'CLOV', 'AGEN', 'GOEV', 'GEVO', 'SENS', 'KSCP', 'ORGN', 'WKHS', 'PDTX', 'LILM', 'DOYU', 'LFWD', 'HOOK']

while (True):
    penny_stock_strat(stocks, datetime.now() - timedelta(minutes=10), datetime.now(), trading_client, market_client, broker_client)
    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))