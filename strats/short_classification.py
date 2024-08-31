from datetime import datetime, timedelta
from helpers import get_data, features, class_model, options, get_data, buy, short_classification, tracker
from messaging import discord
from alpaca.common.exceptions import APIError

import os
import pandas as pd

def generate_model(symbol, model_bars):
    return class_model.create_model(symbol, model_bars, True)

def get_model_bars(symbol, market_client, start, end, time_window):
    bars = get_data.get_bars(symbol, start, end, market_client, time_window)
    bars = features.feature_engineer_df(bars)
    bars = short_classification.classification(bars)
    bars = features.drop_prices(bars)

    buys = len(bars[bars.label == 'buy'])
    sells = len(bars[bars.label == 'sell'])
    holds = (buys + sells) * 2

    bars = pd.concat([
        bars[bars.label == 'buy'],
        bars[bars.label == 'sell'],
        bars[bars.label == 'hold'].sample(n=holds)
    ])

    print(f'Model bars buy count: {buys} sell count: {sells} hold count: {holds}')

    bars['label'] = bars['label'].apply(short_classification.label_to_int)

    return bars

def predict(model, bars):
    pred = model.predict(bars)
    pred = [short_classification.int_to_label(p) for p in pred]
    pred = [s for s in pred if s != 'Hold']
    class_type = "Hold"
    if len(pred) > 0 and all(x == pred[0] for x in pred):
        class_type = "Buy"
        if pred[0] == 'Sell':
            class_type = "Sell"
    return class_type

def classify_symbols(symbols, market_client, end = datetime.now()):
    time_window = int(os.getenv('TIME_WINDOW'))
    day_span = int(os.getenv('SHORT_CLASS_DAY_SPAN'))
    classified = []
    for symbol in symbols:
        bars = get_model_bars(symbol, market_client, end - timedelta(days=day_span), end + timedelta(days=1), time_window)
        model_bars = bars.head(len(bars) - 1)
        pred_bars = bars.tail(1)

        pred_bars.pop("label")

        model = generate_model(symbol, model_bars)

        class_type = predict(model, pred_bars)

        print(f'{symbol} classification={class_type}')

        classified.append({
            'symbol': symbol,
            'class': class_type,
        })

    return classified

def enter(classification, current_positions, trading_client, market_client):
    if classification == "Hold" or next((cp for cp in current_positions if classification['symbol'] in cp.symbol), None) != None:
        return

    is_put = classification['class'] == 'Sell'

    contracts = []

    if classification['class'] == 'Buy':
        contracts = options.get_option_calls(classification['symbol'], market_client, trading_client)
    elif is_put:
        contracts = options.get_option_puts(classification['symbol'], market_client, trading_client)
    
    for contract in contracts:
        # TODO: We can do 0dte, but we need it to be ITM, or before say 2pm
        dte = (contract.expiration_date - datetime.now().date()).days

        if dte >= 1:
            buying_power = get_data.get_buying_power(trading_client)
            qty = options.get_option_buying_power(contract, buying_power, is_put)
            if qty != None and qty > 0:
                discord.send_alpaca_message(f'Bought {qty} of {contract.symbol}')
                buy.submit_order(contract.symbol, qty, trading_client, False)
                break

'''
Three cases for an exit
1. The current cost of the contract(s) is below the defined risk level
2. The model predicts a reverse, we are better off just exiting
3. We are above the defined reward level and a dip occurred - THIS MAY CHANGE A BIT
'''
def exit(position, classifications, trading_client):
    pl = float(position.unrealized_plpc)
    price = float(position.current_price)
    size = float(position.size)
    qty = float(position.qty)
    cost = (price * size) * qty
    contract = position.symbol

    stop_loss = cost * .9
    secure_gains = cost * 1.3

    print(f'{contract} P/L % {pl} stop loss of {stop_loss} and secure gains of {secure_gains}')

    exit = False

    # If we have dropped below the stop loss amount we need to just sell it
    if cost < stop_loss:
        exit = True
    else:
        # See if we are predicting a reverse if so sell it
        classification = next((s for s in classifications if s['symbol'] in contract), None)

        if classification != None:
            if 'C' in contract[5:] and classification['class'] == 'Sell':
                exit = True
            elif 'P' in contract[5:] and classification['class'] == 'Buy':
                exit = True

        # If we are above secure gains and recently had a pull back sell it
        elif cost > secure_gains:
            hst = tracker.get(contract)
            if not hst.empty:
                # TODO: Maybe see about making this a percent barrier, rather than just sell if it dips
                if hst[0]['p/l'] > pl:
                    exit = True

    try:
        if exit:
            trading_client.close_position(contract)
            tracker.clear(contract)
        else:
            # If we don't sell we need to keep track
            tracker.track(contract, pl)
    except APIError as e:
        print(e)