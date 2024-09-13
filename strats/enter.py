from helpers import options, buy, get_data
from messaging import discord
from datetime import datetime

'''
Steps to enter
1. Get a buy or sell signal
2. Get itm or close in the money options
3. If less than 7 dte, buy ITM, if greater OTM is ok
4. Make sure to not risk more than what is configured
'''
def enter_position(classification, current_positions, trading_client, market_client, option_client):
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
        last_quote = options.get_last_quote(contract.symbol, option_client)
        ask_price = last_quote.ask_price
        bid_price = last_quote.bid_price

        print(f'DTE for {contract.symbol} is {dte} at {ask_price}')

        if dte >= 1 and ask_price < 5 and ask_price > 1:
            close_slope = options.get_contract_slope(contract.symbol, -5, option_client)

            if close_slope > 0:
                buying_power = get_data.get_buying_power(trading_client)
                qty = options.get_option_buying_power(contract, buying_power, is_put)
                if qty != None and qty > 0:
                    discord.send_alpaca_message(f'Limit order for {qty}x {contract.symbol} at ask:{ask_price} bid:{bid_price} with slope of {close_slope}')
                    buy.submit_order(contract.symbol, qty, ask_price, trading_client)
                    break