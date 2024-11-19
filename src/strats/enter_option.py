from src.helpers import options, buy, get_data, tracker
from src.messaging import discord
from datetime import datetime

def enter(classification, last_close_underlying, trading_client, option_client):
    symbol = classification['symbol']
    classif = classification['signal']

    if classif == "Hold":
        return

    is_put = classif == 'Sell'

    contract_symbol = options.create_option_symbol(symbol, options.next_friday(datetime.now()), 'P' if is_put else 'C', last_close_underlying)
    last_quote = options.get_option_snap_shot(contract_symbol, option_client)
    ask_price = last_quote.latest_quote.ask_price

    buying_power = get_data.get_buying_power(trading_client)
    qty = options.get_option_buying_power(ask_price, buying_power)
    if qty != None and qty > 0:
        discord.send_alpaca_message(f'Limit order for {qty}x {contract_symbol} at ${ask_price}')
        buy.submit_order(contract_symbol, qty, ask_price, trading_client)
        tracker.track(contract_symbol, 0, ask_price*100)