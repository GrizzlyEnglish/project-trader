from alpaca.trading.enums import AssetClass, AssetStatus, ExerciseStyle
from alpaca.trading.requests import GetOptionContractsRequest
from datetime import datetime, timedelta

import math

def get_option_call(symbol, price, trading_client):
    return get_option(symbol, 'call', 0, price, trading_client)

def get_option_put(symbol, price, trading_client):
    return get_option(symbol, 'put', 0, price, trading_client)

def get_option(symbol, type, current_price, top_price, trading_client):
    if top_price == None or current_price == None:
        return None

    # specify expiration date range
    now = datetime.now()
    until = now + timedelta(days=14)

    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now.strftime(format="%Y-%m-%d"),  
        expiration_date_lte=until.strftime(format="%Y-%m-%d"),  
        root_symbol=symbol,                                    
        type=type,                                          
        #style=ExerciseStyle.AMERICAN,                        
        strike_price_gte=str(current_price),
        strike_price_lte=str(top_price),                               
        limit=100,                                           
        page=None
    )
    return trading_client.get_option_contracts(req)

def get_option_call_itm(symbol, current_price, trading_client):
    if current_price == None:
        return None

    # specify expiration date range
    now = datetime.now()
    until = now + timedelta(days=14)

    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now.strftime(format="%Y-%m-%d"),  
        expiration_date_lte=until.strftime(format="%Y-%m-%d"),  
        root_symbol=symbol,                                    
        type='call',                                          
        strike_price_lte=str(current_price),
        limit=100,                                           
        page=None
    )
    return trading_client.get_option_contracts(req)

def get_option_call_itm(symbol, current_price, trading_client):
    if current_price == None:
        return None

    # specify expiration date range
    now = datetime.now()
    until = now + timedelta(days=14)

    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now.strftime(format="%Y-%m-%d"),  
        expiration_date_lte=until.strftime(format="%Y-%m-%d"),  
        root_symbol=symbol,                                    
        type='put',                                          
        strike_price_gte=str(current_price),
        limit=100,                                           
        page=None
    )
    return trading_client.get_option_contracts(req)

def get_option_buying_power(option_contract, buying_power, is_put):
    o = option_contract
    size = float(o.size)
    close_price = float(o.close_price)
    strike_price = float(o.strike_price)
    option_price = close_price * size
    is_within_bounds = False
    if is_put:
        breakeven_price = strike_price - close_price
    else:
        breakeven_price = close_price + strike_price
    qty = min(math.floor(buying_power / option_price), 2)
    return {
        'qty': qty,
        'breakeven_price': breakeven_price
    }