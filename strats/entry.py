from helpers.get_data import get_buying_power
from helpers.buy import buy_symbol, submit_order
from helpers.options import get_option_call, get_option_put
from helpers.get_data import check_enter_pdt_gaurd, check_option_gaurd
from helpers.features import get_percentage_diff
from messaging.discord import send_alpaca_message
from datetime import datetime

import math
import os

def get_stock_entry(weighted_symbols, weight=0):
    entries = [w for w in weighted_symbols if w['weight'] > weight]
    entries = sorted(entries, key=lambda x: x['weight'], reverse=True) 

    return entries

def get_option_entry(weighted_symbols):
    option_weight = float(os.getenv('OPTION_WEIGHT'))
    entries = [w for w in weighted_symbols if w['abs_weight'] > option_weight]
    entries = sorted(entries, key=lambda x: x['abs_weight'], reverse=False) 

    return entries

def enter(entries, trading_client, market_client):
    buying_power = get_buying_power(trading_client)

    # Remove pdt stuff
    entries = [e for e in entries if not check_enter_pdt_gaurd(e['symbol'], trading_client)]

    # If we have the configured amount buy an option
    option_power = float(os.getenv('OPTION_POWER'))
    if (buying_power > option_power) and not check_option_gaurd(trading_client):
        enter_option(option_power, entries, trading_client, True)

    # Use every last bit
    stock_power = buying_power - option_power
    if stock_power < 0:
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

def enter_option(buying_power, entries, trading_client, send_trade):
    symbols = get_option_entry(entries)
    half_power = buying_power/2

    entered_options = []

    option_gaurd = float(os.getenv('OPTION_GAURD'))

    for e in symbols:
        options = None

        s = e['symbol']
        cp = e['last_close']
        future_close = e['predicted_price'] 

        is_put = cp > future_close and e['weight'] < 0
        shield = future_close

        if is_put:
            option = get_option_put(s, math.floor(future_close), trading_client)
        else:
            option = get_option_call(s, math.ceil(future_close), trading_client)

        if option == None or option.option_contracts == None:
            otype = ''
            if is_put:
                otype = 'put'
            else:
                otype = 'call'
            send_alpaca_message("No %s options for %s with current close at %s and predicted close at %s" % (otype, s, cp, future_close))
            continue

        # Check on the ones with the highest interest
        contracts = [x for x in option.option_contracts if x.open_interest != None]
        contracts.sort(key=lambda x: float(x.open_interest), reverse=True)

        for o in contracts:
            o_buying_power = min(buying_power, half_power)
            dte = (o.expiration_date - datetime.now().date()).days
            if o.close_price != None and o.size != None and dte > 1:
                size = float(o.size)
                close_price = float(o.close_price)
                strike_price = float(o.strike_price)
                option_price = close_price * size
                is_within_bounds = False
                if is_put:
                    breakeven_price = strike_price - close_price
                else:
                    breakeven_price = close_price + strike_price
                qty = min(math.floor(o_buying_power / option_price), 2)
                is_within_bounds = abs(get_percentage_diff(shield, breakeven_price)) <= option_gaurd
                if qty > 0 and is_within_bounds:
                    if send_trade:
                        send_alpaca_message("[ENTER] %s closed: %s predicting close: %s strike: %s break even: %s" % (o.symbol, cp, future_close, strike_price, breakeven_price))
                        submit_order(o.symbol, qty, trading_client)
                    buying_power = buying_power - (option_price * qty)
                    entered_options.append({
                        'option': o.symbol,
                        'symbol': e['symbol'],
                        'qty': qty
                    })
                    break

    return entered_options