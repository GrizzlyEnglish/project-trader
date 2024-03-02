from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

import math

def buy_stocks(stocks_to_buy, trading_client, market_client):
    # after selling get buying power and buy
    account = trading_client.get_account()

    buying_power = account.buying_power

    buying_power_per = float(buying_power) / len(stocks_to_buy)

    print("Current buying power %s and per stock %s" % (buying_power, buying_power_per))

    # Need to determine how much we can afford
    quote_request = StockLatestQuoteRequest(symbol_or_symbols=stocks_to_buy)
    latest_quote = market_client.get_stock_latest_quote(quote_request)

    for stock in stocks_to_buy:
        asset = trading_client.get_asset(stock)

        if not asset.tradable:
            continue

        if latest_quote[stock].ask_price == 0:
            # TODO: Figure out how to handle this case
            continue

        qty = buying_power_per / latest_quote[stock].ask_price

        if not asset.fractionable:
            qty = math.floor(qty)

        if qty <= 0:
            continue

        print("Buying %s of %s" % (qty, stock))

        # preparing market order
        market_order_data = MarketOrderRequest(
                            symbol=stock,
                            qty=qty,
                            side=OrderSide.BUY,
                            type=OrderType.MARKET,
                            time_in_force=TimeInForce.DAY
                            )

        #TODO: Figure out how to reset my buying power in order to not run out before buying them all

        market_order = trading_client.submit_order(order_data=market_order_data)