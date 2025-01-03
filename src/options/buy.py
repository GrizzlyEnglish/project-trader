from alpaca.trading.requests import LimitOrderRequest, ReplaceOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce, OrderType, OrderStatus
from alpaca.common.exceptions import APIError
from src.data import options_data
from src.helpers import tracker, options
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
    
    def cancel_or_replace(self, contract, symbol, ask_price) -> bool:
        # Check if a limit order is already open
        orders = self.trading_client.get_orders()

        for o in orders:
            if o.symbol == contract and o.status != OrderStatus.ACCEPTED:
                # Check if the limit is different
                if float(o.limit_price) != ask_price:
                    discord.send_alpaca_message(f'Replacing limit order for {contract} was ${o.limit_price} now ${ask_price}')
                    self.trading_client.replace_order_by_id(o.id, ReplaceOrderRequest(limit_price=ask_price))
                # we replaced the price or its the same return out dont buy
                return True
            elif o.status == OrderStatus.ACCEPTED:
                underlying = options.get_underlying_symbol(o.symbol)
                if underlying == symbol:
                    self.trading_client.cancel_order_by_id(o.id)
                    discord.send_alpaca_message(f'Cancelling limit order for {contract}')
                    # We are cancelling this and buying a new one dont return

        return False

    def purchase(self, symbol, signal, close, qty) -> None:
        data = options_data.OptionData(symbol, datetime.now(pytz.UTC), 'C' if signal == 'buy' else 'P', close, self.option_client)

        last_quote = data.get_option_snap_shot()
        ask_price = last_quote.latest_quote.ask_price

        try:
            self.cancel_or_replace(data.symbol, symbol, ask_price)
        except Exception as e:
            discord.send_alpaca_message(f'Exception during cancel or replace for {data.symbol}')
        finally:
            qty = self.get_buying_power(ask_price, qty)
            discord.send_alpaca_message(f'Limit order for {qty}x {data.symbol} at ${ask_price}')
            self.submit_order(data.symbol, qty, ask_price, self.trading_client)
            tracker.track(data.symbol, 0, 0, ask_price*100)