from alpaca.trading.enums import AssetClass, AssetStatus, ExerciseStyle
from alpaca.trading.requests import GetOptionContractsRequest
from datetime import datetime, timedelta

def has_open_options(trading_client):
    positions = trading_client.get_all_positions()
    option = next((s for s in positions if s.asset_class == AssetClass.US_OPTION), None)
    return option != None

def get_option_call(symbol, current_price, predicted_price, trading_client):
    return get_option(symbol, 'call', current_price, predicted_price, trading_client)

def get_option_put(symbol, current_price, predicted_price, trading_client):
    return get_option(symbol, 'put', predicted_price, current_price, trading_client)

def get_option(symbol, type, current_price, predicted_price, trading_client):
    # Failed to predict just send empty array
    if predicted_price == None or current_price == None:
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
        strike_price_lte=str(predicted_price),                               
        limit=100,                                           
        page=None
    )
    return trading_client.get_option_contracts(req)