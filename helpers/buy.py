from alpaca.data.requests import StockLatestQuoteRequest, CryptoLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.common.exceptions import APIError
from alpaca.data.historical import StockHistoricalDataClient

import math

def buy_stocks(stocks_to_buy, trading_client, market_client, buying_power):
    amount_to_buy = len(stocks_to_buy)

    if amount_to_buy == 0:
        return

    buying_power_per = 0

    buying_power_per = min(buying_power / 4, 20)

    print("Current buying power %s and max per stock %s" % (buying_power, buying_power_per))

    # Need to determine how much we can afford
    latest_quote = 0
    if (type(market_client) == StockHistoricalDataClient):
        quote_request = StockLatestQuoteRequest(symbol_or_symbols=stocks_to_buy)
        latest_quote = market_client.get_stock_latest_quote(quote_request)
    else:
        quote_request = CryptoLatestQuoteRequest(symbol_or_symbols=stocks_to_buy)
        latest_quote = market_client.get_crypto_latest_quote(quote_request)

    for stock in stocks_to_buy:
        asset = trading_client.get_asset(stock)

        if not asset.tradable:
            print("%s not marked tradeable exiting" % stock)
            continue

        print("%s ask price %s bid price " % (latest_quote[stock].ask_price, latest_quote[stock].bid_price))

        price = latest_quote[stock].ask_price

        if price == 0:
            price = latest_quote[stock].bid_price

        qty = buying_power_per / price

        if not asset.fractionable:
            qty = max(math.floor(qty), 1)
            if (qty * price) > float(buying_power):
                continue

        if qty <= 0:
            continue

        print("Buying %s of %s" % (qty, stock))

        # preparing market order
        if (type(market_client) == StockHistoricalDataClient):
            market_order_data = MarketOrderRequest(
                                symbol=stock,
                                qty=qty,
                                side=OrderSide.BUY,
                                type=OrderType.MARKET,
                                time_in_force=TimeInForce.DAY,
                                )
        else:
            market_order_data = MarketOrderRequest(
                                symbol=stock,
                                qty=qty,
                                side=OrderSide.BUY,
                                type=OrderType.MARKET,
                                time_in_force=TimeInForce.GTC,
                                )

        #TODO: Figure out how to reset my buying power in order to not run out before buying them all

        try:
            market_order = trading_client.submit_order(order_data=market_order_data)
        except APIError as e:
            print(e)