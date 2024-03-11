from alpaca.trading.requests import MarketOrderRequest
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

def sell_stocks(stocks_to_sell, current_positions, trading_client):
    # Sell first to increase buying power
    for stock in stocks_to_sell:

        # make sure we have a poisition
        pos = next((p for p in current_positions if p.symbol == stock), None)

        if (pos == None):
            print("No poistion owned on %s" % stock)
            continue

        # Check for potential profit/loss and try to max/min them
        if (float(pos.unrealized_pl) <= 0):
            print("Holding? Not sure better way to handle for now")
            continue

        print("Selling %s" % stock)

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