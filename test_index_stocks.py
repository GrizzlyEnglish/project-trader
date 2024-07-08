from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from helpers.get_data import get_bars
from dotenv import load_dotenv
from datetime import datetime, timedelta

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

stocks = []

start = datetime.now() - timedelta(days=7)
end = datetime.now()

request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE)
response = trading_client.get_all_assets(request)
stocks = []

for r in response:
    symbol = r.symbol
    bars = get_bars(symbol, start, end, market_client)
    if not bars.empty:
        cost = bars['close'].mean()
        vol = bars['volume'].mean()
        print("%s -- cost: %s vol: %s" % (symbol, cost, vol))
        if cost > 3 and vol > 1000:
            stocks.append({
                'symbol': symbol,
                'cost': cost,
                'vol': vol
            })


print(len(stocks))

stocks.sort(key=lambda x: x['vol'], reverse=True)

stocks = stocks[:100]

with open('stocks.txt', 'w') as file:
    for s in stocks:
        file.write(s['symbol'] + '\n')