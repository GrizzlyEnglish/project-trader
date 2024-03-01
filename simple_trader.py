from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.data.requests import StockLatestQuoteRequest

import pandas as pd

api_key = ''
api_secret = ''

stocks = ['SPY', 'DIS', 'MSFT', 'PXDT', 'VOO', 'WEED', 'BUDZ', 'QUAN', 'AKAM', 'EA', 'GOOGL', 'CART', 'RIVN', 'SOFI', 'EA', 'VB']

# paper=True enables paper trading
trading_client = TradingClient(api_key, api_secret, paper=True)
broker_client = BrokerClient(api_key, api_secret)
market_client = StockHistoricalDataClient(api_key, api_secret)

# Loop stocks
# Buy if 50 day greater than 200 day
# Sell if 50 day less than 200 day

# Current positions we are able to sell
positions = trading_client.get_all_positions()
positions = [{'symbol': p.symbol, 'qty': p.qty_available} for p in positions]

for p in positions:
    print("Current position on %s %s" % (p['symbol'], p['qty']))

buy = []
sell = []

for stock in stocks:
    hist_days = 50
    today = datetime.now()
    n_days_ago = today - timedelta(days=hist_days)
    market_request = StockBarsRequest(symbol_or_symbols=stock,
                            start=n_days_ago,
                            end=today,
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame.Day)
    market_data = market_client.get_stock_bars(market_request)
    market_data_df = market_data.df

    if (market_data_df.empty):
        continue

    three_d_rolling_df = market_data_df['high'].rolling(3).mean() 
    twenty_d_rolling_df = market_data_df['high'].rolling(20).mean() 

    three_d_rolling = three_d_rolling_df.values[-1]
    twenty_d_rolling = twenty_d_rolling_df.values[-1]

    if (three_d_rolling >= twenty_d_rolling):
        print("Setting % s to buy" % stock)
        buy.append(stock)
    else:
        print("Setting % s to sell" % stock)
        sell.append(stock)

# Sell first to increase buying power
for stock in sell:
    # make sure we have a poisition
    if (not any(p['symbol'] == stock for p in positions)):
        continue

    print("Selling %s" % stock)
    position = next((p for p in positions if p['symbol'] == stock), None)

    # preparing market order
    market_order_data = MarketOrderRequest(
                        symbol=position['symbol'],
                        qty=position['qty'],
                        side=OrderSide.SELL,
                        time_in_force=TimeInForce.DAY
                        )

    # Market order
    market_order = trading_client.submit_order(order_data=market_order_data)


# after selling get buying power and buy
account = trading_client.get_account()

buying_power = account.buying_power

buying_power_per = float(buying_power) / len(buy)

print("Current buying power %s and per stock %s" % (buying_power, buying_power_per))

# Need to determine how much we can afford
quote_request = StockLatestQuoteRequest(symbol_or_symbols=stocks)
latest_quote = market_client.get_stock_latest_quote(quote_request)

for stock in buy:
    qty = buying_power_per / latest_quote[stock].bid_price

    print("Buying %s of %s" % (qty, stock))

    # preparing market order
    market_order_data = MarketOrderRequest(
                        symbol=stock,
                        qty=qty,
                        side=OrderSide.BUY,
                        time_in_force=TimeInForce.DAY,
                        type=OrderType.MARKET
                        )

    # Market order
    market_order = trading_client.submit_order(order_data=market_order_data)