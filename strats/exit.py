from helpers.get_data import check_exit_pdt_gaurd
from messaging.discord import send_alpaca_message
from helpers.trend_logic import predict_status

from alpaca.trading.enums import AssetClass

import os

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