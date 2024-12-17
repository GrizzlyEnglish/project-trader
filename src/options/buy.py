from alpaca.trading.requests import LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType
from alpaca.common.exceptions import APIError
from src.data import options_data
from src.helpers import tracker
from src.messaging import discord
from datetime import datetime, timedelta

import os
import math
import pytz

class Buy:

    def __init__(self, trading_client, option_client) -> None:
        self.trading_client = trading_client
        self.option_client = option_client

    def submit_order(self, stock, qty, price, trading_client):
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

    def get_buying_power(self, ask_price, amt):
        option_price = ask_price * 100
        account = self.trading_client.get_account()
        buying_power = float(account.buying_power)
        return min(math.floor(buying_power / option_price), amt)

    def purchase(self, symbol, signal, close, qty) -> None:
        data = options_data.OptionData(symbol, datetime.now(pytz.UTC), 'C' if signal == 'buy' else 'P', close, self.option_client)

        last_quote = data.get_option_snap_shot()
        ask_price = last_quote.latest_quote.ask_price

        qty = self.get_buying_power(ask_price, qty)
        discord.send_alpaca_message(f'Limit order for {qty}x {data.symbol} at ${ask_price}')
        self.submit_order(data.symbol, qty, ask_price, self.trading_client)
        tracker.track(data.symbol, 0, 0, ask_price*100)