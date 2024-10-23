from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.requests import StockLatestTradeRequest, OptionSnapshotRequest
from alpaca.data.historical.option import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta
from src.helpers import features

import os
import math
import numpy as np

def create_option_symbol(underlying, dte, call_put, strike):
    strike_formatted = f"{math.floor(strike):08.3f}".replace('.', '').rjust(8, '0')
    date = dte.strftime("%y%m%d")
    option_symbol = f"{underlying}{date}{call_put}{strike_formatted}"
    
    return option_symbol

def next_friday(date):
    days_until_friday = (4 - date.weekday() + 7) % 7
    days_until_friday = 7 if days_until_friday == 0 else days_until_friday

    return date + timedelta(days=days_until_friday)

def get_underlying_symbol(option_symbol):
    return ''.join([char for char in option_symbol if not char.isdigit()]).rstrip('CP')

def get_option_expiration_date(option_symbol):
    year = int('20' + option_symbol[len(option_symbol)-15:len(option_symbol)-13])
    month = int(option_symbol[len(option_symbol)-13:len(option_symbol)-11])
    day = int(option_symbol[len(option_symbol)-11:len(option_symbol)-9])
    
    return datetime(year, month, day)

def get_contract_slope(contract, bar_amt, option_client):
    bars = get_bars(contract, option_client)
    close_slope = 0

    if not bars.empty:
        # Just want the last few bars
        bars = bars[bar_amt:]
        close_slope = features.slope(np.array(bars['close']))
        print(f'{contract} has a close slope of {close_slope}')
        return close_slope
    
    return 0

def get_bars(contract, start, end, option_client):
    bars = option_client.get_option_bars(OptionBarsRequest(symbol_or_symbols=contract, start=start, end=end, timeframe=TimeFrame(1, TimeFrameUnit.Minute)))
    return bars.df

def get_option_snap_shot(contract, option_client):
    last_quote = option_client.get_option_snapshot(OptionSnapshotRequest(symbol_or_symbols=contract))
    return last_quote[contract]

def get_options(symbol, type, market_client, trading_client):
    quote = market_client.get_stock_latest_trade(StockLatestTradeRequest(symbol_or_symbols=symbol))
    current_price = quote[symbol].price

    if current_price == None:
        return None

    # specify expiration date range
    now = datetime.now()
    until = now + timedelta(days=14)

    var = min(2, current_price * 0.05)
    top = current_price + var
    bottom_out = current_price - var

    print(f'{symbol} option strike top {top} bottom {bottom_out} var {var}')

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
    contracts = sorted(contracts, key=lambda x: (-float(x.strike_price), x.expiration_date)) 

    return contracts

def get_option_puts(symbol, market_client, trading_client):
    contracts = get_options(symbol, 'put', market_client, trading_client)
    contracts = sorted(contracts, key=lambda x: (float(x.strike_price), x.expiration_date)) 

    return contracts

def get_option_buying_power(ask_price, buying_power):
    amt = int(os.getenv('BUY_AMOUNT'))

    option_price = ask_price * 100
    return min(math.floor(buying_power / option_price), amt)