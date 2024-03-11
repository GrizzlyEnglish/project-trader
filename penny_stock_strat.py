from alpaca.data import TimeFrame 
from alpaca.data.requests import StockBarsRequest

 
import sys
sys.path.append('../helpers')
 
from helpers.buy import buy_stocks
from helpers.sell import sell_stocks
from helpers.start_logic import determine_status
from generate_model import generate_model

def penny_stock_strat(stocks, window_start, window_end, trading_client, market_client, broker_client):
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

        model = generate_model(stock, market_client)

        status = determine_status(window_data_df, model)

        if status == 'buy':
            print("Setting % s to buy" % stock)
            buy.append(stock)
        elif status == 'sell':
            print("Setting % s to sell" % stock)
            sell.append(stock)
        else :
            print("Holding %s" % stock)

    sell_stocks(sell, positions, trading_client)

    buy_stocks(buy, trading_client, market_client)