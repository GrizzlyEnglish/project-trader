from helpers.get_data import position_sellable
from helpers.sell import sell_symbol
from messaging.discord import send_alpaca_message
from helpers.trend_logic import predict_status

import os

def get_exit_symbols(weighted_symbols):
    entries = [w for w in weighted_symbols if w['weight'] < 0]
    entries = sorted(entries, key=lambda x: x['weight'], reverse=False) 

    return entries

def exit(entries, trading_client, market_client):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for position in current_positions:
        pl = float(position.unrealized_plpc)

        current_trend = next((s for s in entries if s['symbol'].replace("/", "") == position.symbol), None)
        
        if current_trend == None or not position_sellable(position.symbol, trading_client):
            # If no trend somehow, or we bought it today just return
            return
        
        current_weight = current_trend['weight']

        sell = False
        message = ""

        if current_weight < -10 and pl > 0:
            # Very good chance this is the best time to exit
            message = "[EXIT] Exiting %s with a weight of %s" % (position.symbol, current_weight)
            sell = True
        elif current_weight <= 0:
            # Not sure, let us predict the price and see if we should
            prediction = predict_status(position.symbol, market_client)
            if prediction != None and (prediction['predicted_cross'] == "sell" or prediction['predicted_price'] == "sell"):
                # The model is predicting a cross and a dip in price let us just sell it
                message = "[EXIT] Exiting %s with a weight of %s, close of %s, and a predicted future price of %s" % (position.symbol, current_weight, current_trend['last_close'], prediction['future_close'])
                sell = True
        
        if not sell and pl < stop_loss:
            sell = True
            message = "[EXIT] Forcing the exit of %s due to stop loss. Something was wrong with the trends" % position.symbol

        if sell:
            try:
                sell_symbol(position.symbol, trading_client)
            except Exception as e:
                message = e

        send_alpaca_message(message)