from src.helpers import options, buy, get_data
from src.messaging import discord
from datetime import datetime

'''
Steps to enter
1. Get a buy or sell signal
2. Get itm or close in the money options
3. If less than 7 dte, buy ITM, if greater OTM is ok
4. Make sure to not risk more than what is configured
'''
def enter_position(classification, current_positions, trading_client, market_client, option_client):
    symbol = classification['symbol']
    classif = classification['class']
    expected_move = classification['expected_move']

    if classif == "Hold" or next((cp for cp in current_positions if symbol in cp.symbol), None) != None:
        return

    is_put = classif == 'Sell'

    contracts = []

    if not is_put:
        contracts = options.get_option_calls(symbol, market_client, trading_client)
    else:
        contracts = options.get_option_puts(symbol, market_client, trading_client)
    
    for contract in contracts:
        dte = (contract.expiration_date - datetime.now().date()).days
        last_quote = options.get_option_snap_shot(contract.symbol, option_client)
        ask_price = last_quote.latest_quote.ask_price
        bid_price = last_quote.latest_quote.bid_price
        strike_price = contract.strike_price
        underlying_price = get_data.get_stock_price(symbol, market_client)

        do_enter_position, expected_contract_price = check_contract_entry(contract.symbol, contract.type, strike_price, ask_price, bid_price, last_quote.implied_volatility, dte, underlying_price, expected_move)

        if do_enter_position:
            buying_power = get_data.get_buying_power(trading_client)
            qty = options.get_option_buying_power(contract, buying_power, is_put)
            if qty != None and qty > 0:
                discord.send_alpaca_message(f'Limit order for {qty}x {contract.symbol} at ${ask_price}, expected to reach ${expected_contract_price}')
                buy.submit_order(contract.symbol, qty, ask_price, trading_client)
                break

def check_contract_entry(contract, contract_type, strike_price, ask_price, bid_price, iv, dte, underlying_price, expected_diff):
    stop_loss, secure_gains = options.determine_risk_reward(ask_price*100)

    contract_price = options.get_option_price(contract_type, underlying_price, strike_price, dte, 0.05, iv)
    expected_contract_price = options.get_option_price(contract_type, underlying_price * (1+expected_diff), strike_price, dte, 0.05, iv) 
    expected_contract_cost = expected_contract_price * 100

    print(f'{contract} with {dte} dte and spread {ask_price}/{bid_price} cost {contract_price} expected contract cost {expected_contract_cost} vs {secure_gains}')

    return expected_contract_cost >= secure_gains, expected_contract_price


