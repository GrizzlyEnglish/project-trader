from src.helpers import options, buy, get_data, tracker
from src.messaging import discord
from datetime import datetime

def enter(classification, trading_client, market_client, option_client):
    symbol = classification['symbol']
    classif = classification['signal']

    if classif == "Hold":
        return

    is_put = classif == 'Sell'

    contracts = []

    if not is_put:
        contracts = options.get_option_calls(symbol, market_client, trading_client)
    else:
        contracts = options.get_option_puts(symbol, market_client, trading_client)
    
    for contract in contracts:
        last_quote = options.get_option_snap_shot(contract.symbol, option_client)
        ask_price = last_quote.latest_quote.ask_price

        if ask_price < 3 and ask_price > 1:
            buying_power = get_data.get_buying_power(trading_client)
            qty = options.get_option_buying_power(contract, buying_power, is_put)
            if qty != None and qty > 0:
                discord.send_alpaca_message(f'Limit order for {qty}x {contract.symbol} at ${ask_price}')
                buy.submit_order(contract.symbol, qty, ask_price, trading_client)
                tracker.track(contract.symbol, 0, ask_price*100)
                break