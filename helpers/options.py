from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.requests import StockLatestTradeRequest
from datetime import datetime, timedelta

import math

def get_options(symbol, type, market_client, trading_client):
    quote = market_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=symbol))
    current_price = quote[symbol].price

    if current_price == None:
        return None

    # specify expiration date range
    now = datetime.now()
    until = now + timedelta(days=14)

    top = current_price * 1.15
    bottom_out = current_price * 0.9

    print(f'{symbol} option strike top {top} bottom {bottom_out}')

    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now.strftime(format="%Y-%m-%d"),  
        expiration_date_lte=until.strftime(format="%Y-%m-%d"),  
        root_symbol=symbol,                                    
        type=type,                                          
        strike_price_lte=str(top),
        strike_price_gte=str(bottom_out),
        limit=100,                                           
        page=None
    )

    contracts = trading_client.get_option_contracts(req).option_contracts
    return [c for c in contracts if c.open_interest != None and c.close_price != None]

def get_option_calls(symbol, market_client, trading_client):
    contracts = get_options(symbol, 'call', market_client, trading_client)
    contracts = sorted(contracts, key=lambda x: float(x.strike_price), reverse=False) 

    return contracts

def get_option_puts(symbol, market_client, trading_client):
    contracts = get_options(symbol, 'put', market_client, trading_client)
    contracts = sorted(contracts, key=lambda x: float(x.strike_price), reverse=True) 

    return contracts

def get_option_buying_power(option_contract, buying_power, is_put):
    o = option_contract

    size = float(o.size)
    if o.close_price == None:
        return None
    else:
        close_price = float(o.close_price)

    option_price = close_price * size

    return min(math.floor(buying_power / option_price), 2)