from alpaca.trading.requests import MarketOrderRequest
from alpaca.common.exceptions import APIError
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType

def sell_symbol(position, trading_client):
    time_in_force = TimeInForce.DAY

    # preparing market order
    market_order_data = MarketOrderRequest(
                        symbol=position.symbol,
                        qty=position.qty,
                        side=OrderSide.SELL,
                        time_in_force=time_in_force
                        )

    return trading_client.submit_order(order_data=market_order_data)