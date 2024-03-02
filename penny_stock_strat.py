from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta

from buy import buy_stocks
from sell import sell_stocks

import pandas as pd

#TODO: Move to env vars?
api_key = ''
api_secret = ''

stocks = ['FSR', 'NKLA', 'BKKT', 'OPK', 'CLOV', 'AGEN', 'GOEV', 'GEVO', 'SENS', 'KSCP', 'ORGN', 'WKHS', 'PDTX', 'LILM', 'DOYU', 'LFWD', 'HOOK']

# paper=True enables paper trading
trading_client = TradingClient(api_key, api_secret, paper=True)
broker_client = BrokerClient(api_key, api_secret)
market_client = StockHistoricalDataClient(api_key, api_secret)

# Current positions we are able to sell
positions = trading_client.get_all_positions()
positions = [{'symbol': p.symbol, 'qty': p.qty_available} for p in positions]

for p in positions:
    print("Current position on %s %s" % (p['symbol'], p['qty']))

buy = []
sell = []

for stock in stocks:
    hst = 50
    end = datetime.now()
    start = end - timedelta(hours=hst)
    market_request = StockBarsRequest(symbol_or_symbols=stock,
                            start=start,
                            end=end,
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame.Hour)
    market_data = market_client.get_stock_bars(market_request)
    market_data_df = market_data.df

    if (market_data_df.empty):
        continue

    small_rolling_df = market_data_df['high'].rolling(3).mean() 
    large_rolling_df = market_data_df['high'].rolling(20).mean() 

    small_rolling = small_rolling_df.values[-1]
    large_rolling = large_rolling_df.values[-1]

    if (small_rolling >= large_rolling):
        print("Setting % s to buy" % stock)
        buy.append(stock)
    else:
        print("Setting % s to sell" % stock)
        sell.append(stock)

sell_stocks(sell, positions, trading_client)

buy_stocks(buy, trading_client, market_client)