from alpaca.trading.requests import MarketOrderRequest
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

def sell_symbol(symbols_to_sell, trading_client):
    # Current positions we are able to sell
    current_positions = trading_client.get_all_positions()

    for p in current_positions:
        print("Current position on %s %s with a p/l of %s" % (p.symbol, p.qty, p.unrealized_pl))

    # Sell first to increase buying power
    for symbol in symbols_to_sell:

        # make sure we have a poisition
        pos = next((p for p in current_positions if p.symbol == symbol), None)

        if (pos == None):
            print("No poistion owned on %s" % symbol)
            continue

        # Check for potential profit/loss and try to max/min them
        if (float(pos.unrealized_pl) <= 0):
            print("Holding? Not sure better way to handle for now")
            continue

        print("Selling %s" % symbol)

        # preparing market order
        market_order_data = MarketOrderRequest(
                            symbol=pos.symbol,
                            qty=pos.qty,
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )

        # Market order
        try:
            market_order = trading_client.submit_order(order_data=market_order_data)
        except APIError as e:
            print(e)