from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta

from buy import buy_stocks
from sell import sell_stocks
from determine_trend import determine_trend

import pandas as pd
import time

#TODO: Move to env vars?
api_key = ''
api_secret = ''

#stocks = ['FSR', 'NKLA', 'BKKT', 'OPK', 'CLOV', 'AGEN', 'GOEV', 'GEVO', 'SENS', 'KSCP', 'ORGN', 'WKHS', 'PXDT', 'LILM', 'DOYU', 'LFWD', 'HOOK']
stocks = ['LILM']
sleep_time = 60

window_in_min = 10
rolling_small_window = 2
rolling_large_window = 6

# paper=True enables paper trading
trading_client = TradingClient(api_key, api_secret, paper=True)
broker_client = BrokerClient(api_key, api_secret)
market_client = StockHistoricalDataClient(api_key, api_secret)

while (True):

    # Current positions we are able to sell
    positions = trading_client.get_all_positions()

    for p in positions:
        print("Current position on %s %s with a p/l of %s" % (p.symbol, p.qty, p.unrealized_pl))

    buy = []
    sell = []

    for stock in stocks:
        # Critera
        # Buy - Downward trend with a slight upward
        # Sell - Upward trend with a slight downard
        print('--------- Checking trend for %s ------------' % stock)

        small_window_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=stock,
                                start=datetime.now() - timedelta(minutes=window_in_min),
                                end=datetime.now(),
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))

        large_window_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=stock,
                                start=datetime.now() - timedelta(minutes=(window_in_min*2)),
                                end=datetime.now() - timedelta(minutes=window_in_min),
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))


        small_window_data_df = small_window_data.df
        large_window_data_df = large_window_data.df

        if (small_window_data_df.empty or large_window_data_df.empty):
            print("No df for %s" % stock)
            continue

        # Determine large window trend
        large_low_df = large_window_data_df['low']
        large_trend = determine_trend(large_low_df, rolling_small_window, rolling_large_window)

        # Determine small window trend
        small_low_df = small_window_data_df['low']
        small_trend = determine_trend(small_low_df, rolling_small_window, rolling_large_window)

        if large_trend == 'down' and small_trend == 'up':
            print("Setting % s to buy" % stock)
            buy.append(stock)
        elif large_trend == 'up' and small_trend == 'down':
            print("Setting % s to sell" % stock)
            sell.append(stock)
        else :
            print("Hold %s current large trend is %s and small trend is %s" % (stock, large_trend, small_trend))

    sell_stocks(sell, positions, trading_client)

    buy_stocks(buy, trading_client, market_client)

    print("Sleeping for %s" % str(sleep_time))
    time.sleep(sleep_time)