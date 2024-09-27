from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.data.requests import StockLatestTradeRequest, OptionSnapshotRequest
from alpaca.data.historical.option import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from src.helpers import features

import math
import numpy as np
import scipy.optimize as opt
import QuantLib as ql 

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

def get_bars(contract, option_client):
    bars = option_client.get_option_bars(OptionBarsRequest(symbol_or_symbols=contract, timeframe=TimeFrame.Minute))
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

def get_option_buying_power(option_contract, buying_power, is_put):
    o = option_contract

    size = float(o.size)
    if o.close_price == None:
        return None
    else:
        close_price = float(o.close_price)

    option_price = close_price * size

    return min(math.floor(buying_power / option_price), 2)

def determine_risk_reward(cost):
    risk = min(cost * .15, 100)
    stop_loss = cost - risk
    secure_gains = cost + (risk * 3)

    return stop_loss, secure_gains

def get_option_price(option_type, underlying_price, strike_price, dte, risk_free_rate, volatility):
    m = datetime.now() + timedelta(days=dte)
    maturity_date = ql.Date(m.strftime('%d-%m-%Y'), '%d-%m-%Y')
    calculation_date = ql.Date.todaysDate()
    spot_price = underlying_price 
    dividend_rate =  0

    if option_type == 'call':
        option_type = ql.Option.Call
    else:
        option_type = ql.Option.Put

    day_count = ql.Actual365Fixed()
    calendar = ql.UnitedStates(ql.UnitedStates.NYSE)

    ql.Settings.instance().evaluationDate = calculation_date

    payoff = ql.PlainVanillaPayoff(option_type, strike_price)
    settlement = calculation_date

    am_exercise = ql.AmericanExercise(settlement, maturity_date)
    american_option = ql.VanillaOption(payoff, am_exercise)

    spot_handle = ql.QuoteHandle(
        ql.SimpleQuote(spot_price)
    )
    flat_ts = ql.YieldTermStructureHandle(
        ql.FlatForward(calculation_date, risk_free_rate, day_count)
    )
    dividend_yield = ql.YieldTermStructureHandle(
        ql.FlatForward(calculation_date, dividend_rate, day_count)
    )
    flat_vol_ts = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(calculation_date, calendar, volatility, day_count)
    )
    bsm_process = ql.BlackScholesMertonProcess(spot_handle, 
                                            dividend_yield, 
                                            flat_ts, 
                                            flat_vol_ts)

    steps = 200
    binomial_engine = ql.BinomialVanillaEngine(bsm_process, "crr", steps)
    american_option.setPricingEngine(binomial_engine)
    return american_option.NPV()