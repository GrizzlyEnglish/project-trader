from alpaca.trading.client import TradingClient
from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange
from dotenv import load_dotenv
from helpers.get_data import get_bars
from datetime import timedelta, datetime
from helpers.generate_model import generate_model
from strat import filter_strat

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
stock_discord_url = os.getenv('STOCK_DISCORD_URL')
crypto_discord_url = os.getenv('CRYPTO_DISCORD_URL')
alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')

days = float(os.getenv('FULL_DAY_COUNT'))
start = datetime.now()
count = 0

trading_client = TradingClient(api_key, api_secret, paper=paper)
crypto_market_client = CryptoHistoricalDataClient(api_key, api_secret)
stock_market_client = StockHistoricalDataClient(api_key, api_secret)

request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE, exchange=AssetExchange.NYSE)
response = trading_client.get_all_assets(request)
stocks = [s.symbol for s in response if filter_strat(s.symbol, stock_market_client, start)]

with open('stocks.txt', 'w') as file:
    for s in stocks:
        file.write(s + '\n')

print(len(stocks))

for s in stocks:
    try:
        full_bars = get_bars(s, start - timedelta(days=days), start, stock_market_client)
        generate_model(s, full_bars)
    except Exception as e:
        print(e)