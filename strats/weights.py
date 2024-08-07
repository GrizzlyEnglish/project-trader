from helpers.get_data import get_buying_power
from helpers.buy import buy_symbol, submit_order
from helpers.options import get_option_call, get_option_put, get_option_buying_power
from helpers.get_data import check_enter_pdt_gaurd, check_option_gaurd
from helpers.features import get_percentage_diff
from messaging.discord import send_alpaca_message
from datetime import datetime
from helpers.get_data import check_exit_pdt_gaurd
from alpaca.trading.enums import AssetClass

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
    enter_option(buying_power, option_power, entries, trading_client, True)

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

def enter_option(buying_power, option_power, entries, trading_client, send_trade):
    symbols = get_option_entry(entries)

    option_gaurd = float(os.getenv('OPTION_GAURD'))

    collected_contracts = []

    for e in symbols:
        s = e['symbol']
        cp = e['last_close']
        future_close = e['predicted_price'] 

        if e['abs_weight'] < 8:
            continue

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
        contracts = [x for x in option.option_contracts if x.open_interest != None and float(x.open_interest) > 500]
        collected_contracts = collected_contracts + contracts

    # Enter the top contracts
    collected_contracts.sort(key=lambda x: float(x.open_interest), reverse=True)
    entered_options = []
    for o in contracts:
        buying_power = get_buying_power(trading_client)

        if not (buying_power > option_power) or check_option_gaurd(trading_client):
            return entered_options

        half_power = buying_power/2
        o_buying_power = min(buying_power, half_power)
        dte = (o.expiration_date - datetime.now().date()).days
        if o.close_price != None and o.size != None and dte > 1:
            is_within_bounds = False
            power = get_option_buying_power(o, o_buying_power, is_put)
            breakeven_price = power['breakeven_price']
            qty = power['qty']
            is_within_bounds = abs(get_percentage_diff(shield, breakeven_price)) <= option_gaurd
            if qty > 0 and is_within_bounds:
                if send_trade:
                    send_alpaca_message("[ENTER] %s closed: %s predicting close: %s strike: %s break even: %s" % (o.symbol, cp, future_close, float(o.strike_price), breakeven_price))
                    submit_order(o.symbol, qty, trading_client)
                entered_options.append({
                    'option': o.symbol,
                    'symbol': o.root_symbol,
                    'qty': qty
                })
                break

    return entered_options

def get_exit_symbols(weighted_symbols):
    entries = [w for w in weighted_symbols if w['weight'] < 0]
    entries = sorted(entries, key=lambda x: x['weight'], reverse=False) 

    return entries

def determine_if_exiting(symbol, current_trend, pl, stop_loss):
    current_weight = current_trend['weight']
    future_close = current_trend['predicted_price']
    predicted_cross = current_trend['predicted_cross']
    predicted_status = current_trend['predicted_status']

    sell = False
    message = ""

    if current_weight < -10 and pl > 0:
        # Very good chance this is the best time to exit
        message = "[EXIT] Exiting %s with a weight of %s" % (symbol, current_weight)
        sell = True
    elif current_weight <= 0:
        # Not sure, let us check the predict price and see if we should
        if predicted_cross == "sell" or predicted_status == "sell":
            # The model is predicting a cross and a dip in price let us just sell it
            message = "[EXIT] Exiting %s with a weight of %s, close of %s, and a predicted future price of %s" % (symbol, current_weight, current_trend['last_close'], future_close)
            sell = True
    
    if not sell and pl < stop_loss:
        sell = True
        message = "[EXIT] Forcing the exit of %s due to stop loss. Something was wrong with the trends" % symbol

    return {
        'sell': sell,
        'message': message,
        'predicted_close': future_close
    }

def exit(entries, trading_client):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for position in current_positions:
        pl = float(position.unrealized_plpc)
        symbol = position.symbol
        sell_symbol = symbol

        if position.asset_class == AssetClass.US_OPTION:
            contract = trading_client.get_option_contract(symbol)
            symbol = contract.underlying_symbol

        current_trend = next((s for s in entries if s['symbol'].replace("/", "") == symbol), None)
        
        if current_trend == None or check_exit_pdt_gaurd(symbol, trading_client):
            # If no trend somehow, or we bought it today just return
            print("Can't sell %s bought within 12 hours or there is no trend" % symbol)
            continue
        
        status = determine_if_exiting(symbol, current_trend, pl, stop_loss)

        if status['sell']:
            message = status['message']
            try:
                trading_client.close_position(sell_symbol)
            except Exception as e:
                print(e)
                message = "Error occurred trying to exit"

            send_alpaca_message(message)