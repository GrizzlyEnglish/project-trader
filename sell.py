from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

def sell_stocks(stocks_to_sell, current_positions, trading_client):
    # Sell first to increase buying power
    for stock in stocks_to_sell:
        # make sure we have a poisition
        if (not any(p['symbol'] == stock for p in current_positions)):
            continue

        print("Selling %s" % stock)
        position = next((p for p in current_positions if p['symbol'] == stock), None)

        # preparing market order
        market_order_data = MarketOrderRequest(
                            symbol=position['symbol'],
                            qty=position['qty'],
                            side=OrderSide.SELL,
                            time_in_force=TimeInForce.DAY
                            )

        # Market order
        market_order = trading_client.submit_order(order_data=market_order_data)