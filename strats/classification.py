from datetime import datetime, timedelta
from helpers import get_data, features, class_model, options, get_data, buy
from messaging import discord
from alpaca.common.exceptions import APIError

import os

def generate_model(symbol, market_client, start, end, time_window):
    bars = get_data.get_bars(symbol, start, end, market_client, time_window)
    bars = features.feature_engineer_df(bars)
    bars = features.classification(bars)
    bars = features.drop_prices(bars)

    model_bars = bars.head(len(bars) - 1)

    return class_model.create_model(symbol, model_bars, True)

def predict(model, bars):
    pred = model.predict(bars)
    pred = [features.int_to_label(p) for p in pred]
    pred = [s for s in pred if s != 'Hold']
    class_type = "Hold"
    if len(pred) > 0 and all(x == pred[0] for x in pred):
        class_type = "Buy"
        if pred[0] == 'Sell':
            class_type = "Sell"
    return class_type

def classify_symbols(symbols, market_client, end = datetime.now(), time_window = 15):
    classified = []
    for symbol in symbols:
        model = generate_model(symbol, market_client, end - timedelta(days=60), end + timedelta(days=1), time_window)

        bars = get_data.get_bars(symbol, end - timedelta(hours=1), end, market_client, time_window)
        pred_bars = bars.tail(1)

        class_type = predict(model, bars)
        price = pred_bars["close"].iloc[-1]

        print(f'{symbol} prediction: {class_type}')

        classified.append({
            'symbol': symbol,
            'class': class_type,
            'price': price 
        })

    return classified

def enter(classification, current_positions, trading_client):
    is_put = classification['class'] == 'Sell'

    contracts = []

    if classification['class'] == 'Buy':
        contracts = options.get_option_call_itm(classification['symbol'], classification['price'], trading_client)[-1:]
    elif is_put:
        contracts = options.get_option_put_itm(classification['symbol'], classification['price'], trading_client)[:1]
    
    for contract in contracts:
        owned = next((cp for cp in current_positions if classification['symbol'] in cp.symbol), None)

        if owned == None:
            buying_power = get_data.get_buying_power(trading_client)
            qty = options.get_option_buying_power(contract, buying_power, is_put)['qty']
            if qty != None and qty > 0:
                discord.send_alpaca_message(f'Bought {qty} of {contract.symbol}')
                buy.submit_order(contract.symbol, qty, trading_client, False)

def exit(position, classifications, trading_client):
    stop_loss = float(os.getenv('STOP_LOSS'))
    secure_gains = float(os.getenv('SECURE_GAINS'))

    pl = float(position.unrealized_plpc)
    contract = position.symbol

    print(f'{contract} P/L % {pl}')

    exit = False
    classification = next((s for s in classifications if s['symbol'] in contract), None)

    if classification != None:
        symbol = classification['symbol']
        if classification['class'] == 'Sell' and pl < 0:
            exit = True

    if pl < -stop_loss: 
        exit = True
    elif pl > secure_gains:
        exit = True

    if exit:
        try:
            trading_client.close_position(contract)
        except APIError as e:
            print(e)