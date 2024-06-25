from helpers.get_data import get_buying_power
from helpers.buy import buy_symbol, submit_order
from helpers.options import has_open_options, get_option_call, get_option_put
from helpers.trend_logic import get_predicted_price
from messaging.discord import send_alpaca_message
from helpers.get_data import check_enter_pdt_gaurd

import math
import os

def get_stock_entry(weighted_symbols, weight=0):
    entries = [w for w in weighted_symbols if w['weight'] > weight]
    entries = sorted(entries, key=lambda x: x['weight'], reverse=True) 

    return entries

def get_option_entry(weighted_symbols):
    option_weight = 8
    entries = [w for w in weighted_symbols if w['abs_weight'] > option_weight]
    entries = sorted(entries, key=lambda x: x['abs_weight'], reverse=False) 

    return entries

def enter(entries, trading_client, market_client):
    buying_power = get_buying_power(trading_client)

    # Remove pdt stuff
    entries = [e for e in entries if not check_enter_pdt_gaurd(e['symbol'], trading_client)]

    # If we have the configured amount buy an option
    option_power = float(os.getenv('OPTION_POWER'))
    if buying_power > option_power:
        enter_option(option_power, entries, trading_client, market_client, True)

    # Use every last bit
    stock_power = buying_power - option_power
    if stock_power > 0:
        stock_power = buying_power

    if stock_power > 0:
        enter_stock(stock_power, entries, trading_client, market_client)

def enter_stock(buying_power, entries, trading_client, market_client):
    if buying_power > 0:
        symbols = get_stock_entry(entries, 7)
        for s in symbols:
            buying_power_per = min(buying_power / 4, 50)

            if buying_power <= 1:
                return

            bought = buy_symbol(s['symbol'], trading_client, market_client, buying_power_per)

            if bought:
                buying_power = buying_power - buying_power_per

def enter_option(buying_power, entries, trading_client, market_client, send_trade):
    symbols = get_option_entry(entries)
    half_power = buying_power/2

    options = []

    for e in symbols:
        options = None

        s = e['symbol']
        cp = e['last_close']
        future_close = get_predicted_price(s, market_client)

        print("Looking for options for %s between %s and %s" % (s, cp, future_close))

        is_put = cp > future_close and e['weight'] < 0
        shield = None

        if is_put:
            options = get_option_put(s, cp, future_close, trading_client)
            shield = future_close
        else:
            options = get_option_call(s, cp, future_close, trading_client)
            shield = cp

        if options == None:
            print("No options for %s with current close at %s and predicted close at %s" % (s, cp, future_close))
            continue

        for o in options.option_contracts:
            o_buying_power = min(buying_power, half_power)
            if o.close_price != None and o.size != None and o.open_interest != None:
                size = float(o.size)
                close_price = float(o.close_price)
                strike_price = float(o.strike_price)
                option_price = close_price * size
                is_within_bounds = False
                if is_put:
                    breakeven_price = strike_price - close_price
                    is_within_bounds = breakeven_price <= shield
                else:
                    breakeven_price = close_price + strike_price
                    is_within_bounds = breakeven_price >= shield
                qty = math.floor(o_buying_power / option_price)
                send_alpaca_message("[ENTER] Option %s closed at %s with strike of %s and break even of %s" % (o.symbol, close_price, strike_price, breakeven_price))
                if qty > 0 and is_within_bounds:
                    if send_trade:
                        submit_order(o.symbol, qty, trading_client)
                    buying_power = buying_power - (option_price * qty)
                    options.append({
                        'option': o.symbol,
                        'symbol': e['symbol'],
                        'qty': qty
                    })

    return options