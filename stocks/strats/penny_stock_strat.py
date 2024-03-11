from alpaca.trading.client import TradingClient
from alpaca.broker import BrokerClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta

from helpers.buy import buy_stocks
from helpers.sell import sell_stocks
from helpers.start_logic import determine_status

def penny_stock_strat(stocks, window_start, window_end, emw_span, api_key, api_secret, paper):
    # paper=True enables paper trading
    trading_client = TradingClient(api_key, api_secret, paper=paper)
    broker_client = BrokerClient(api_key, api_secret)
    market_client = StockHistoricalDataClient(api_key, api_secret)

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

        # TODO: Run through a model to determine
        trade_factor = 0.003

        window_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=stock,
                                start=window_start,
                                end=window_end,
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))

        window_data_df = window_data.df

        if (window_data_df.empty):
            print("No df for %s" % stock)
            continue

        status = determine_status(window_data_df, 'close', emw_span, trade_factor)

        '''
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

        '''