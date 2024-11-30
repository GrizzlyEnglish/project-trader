from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.common.exceptions import APIError
from src.helpers import options, get_data, buy, tracker
from src.messaging import discord
from datetime import datetime

import os
import math

class Buy:

    def __init__(self, trading_client, option_client) -> None:
        self.trading_client = trading_client
        self.option_client = option_client

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

    def get_buying_power(ask_price, buying_power):
        amt = int(os.getenv('BUY_AMOUNT'))

        option_price = ask_price * 100
        return min(math.floor(buying_power / option_price), amt)

    def purchase(self, classification, last_close_underlying) -> None:
        symbol = classification['symbol']
        classif = classification['signal']

        if classif == "Hold":
            return

        is_put = classif == 'Sell'

        # TODO: Fix this
        '''
        contract_symbol = options.create_option_symbol(symbol, options.next_friday(datetime.now()), 'P' if is_put else 'C', last_close_underlying)
        last_quote = options.get_option_snap_shot(contract_symbol, self.option_client)
        ask_price = last_quote.latest_quote.ask_price

        buying_power = get_data.get_buying_power(self.trading_client)
        qty = options.get_option_buying_power(ask_price, buying_power)
        if qty != None and qty > 0:
            discord.send_alpaca_message(f'Limit order for {qty}x {contract_symbol} at ${ask_price}')
            self.submit_order(contract_symbol, qty, ask_price, self.trading_client)
            tracker.track(contract_symbol, 0, ask_price*100)
        '''