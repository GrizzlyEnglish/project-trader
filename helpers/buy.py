from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.common.exceptions import APIError
from messaging.discord import send_alpaca_message

import math

def buy_symbol(stock, trading_client, market_client, buying_power):
    print("Current buying power %s and max per stock %s" % (buying_power, buying_power))

    # Need to determine how much we can afford
    latest_quote = 0
    quote_request = StockLatestQuoteRequest(symbol_or_symbols=stock)
    latest_quote = market_client.get_stock_latest_quote(quote_request)

    try:
        asset = trading_client.get_asset(stock)
    except APIError as e:
        print(e)
        return

    if not asset.tradable:
        print("%s not marked tradeable exiting" % stock)
        return

    print("%s ask price %s bid price " % (latest_quote[stock].ask_price, latest_quote[stock].bid_price))

    price = latest_quote[stock].bid_price

    if price == 0:
        price = latest_quote[stock].bid_price

    qty = buying_power / price

    if not asset.fractionable:
        qty = max(math.floor(qty), 1)
        if (qty * price) > float(buying_power):
            return buying_power

    if qty < 1:
        return buying_power

    return submit_order(stock, qty, trading_client)

def submit_order(stock, qty, price, trading_client):
    market_order_data = LimitOrderRequest(
                        symbol=stock,
                        qty=qty,
                        limit_price=price,
                        side=OrderSide.BUY,
                        type=OrderType.MARKET,
                        time_in_force=TimeInForce.DAY,
                        )

    try:
        market_order = trading_client.submit_order(order_data=market_order_data)

        price = market_order.filled_avg_price

        if price == None:
            price = "unknown"

        return True
    except APIError as e:
        print(e)
        return False