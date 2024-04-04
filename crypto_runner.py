from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import CryptoHistoricalDataClient 
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from dotenv import load_dotenv
from crypto_start import crypto_strat

import os
import time

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
broker_client = BrokerClient(api_key, api_secret)
market_client = CryptoHistoricalDataClient(api_key, api_secret)

request = GetAssetsRequest(asset_class=AssetClass.CRYPTO)
response = trading_client.get_all_assets(request)
coins = [c.symbol for c in response if c.symbol.endswith('/USD')]

while (True):
    crypto_strat(coins, trading_client, market_client)
    print("Sleeping for %s" % str(sleep_time))
    time.sleep(int(sleep_time))