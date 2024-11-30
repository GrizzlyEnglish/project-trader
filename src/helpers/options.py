from alpaca.trading.enums import AssetStatus
from alpaca.trading.requests import GetOptionContractsRequest
from datetime import datetime, timedelta
from src.helpers import features

import os
import math
import numpy as np

def next_friday(date):
    days_until_friday = (4 - date.weekday() + 7) % 7
    days_until_friday = 7 if days_until_friday == 0 else days_until_friday

    return date + timedelta(days=days_until_friday)

def create_option_symbol(underlying, dte, call_put, strike) -> str:
    strike_formatted = f"{strike:08.3f}".replace('.', '').rjust(8, '0')
    date = dte.strftime("%y%m%d")
    return f"{underlying}{date}{call_put}{strike_formatted}"

def get_underlying_symbol(option_symbol):
    return ''.join([char for char in option_symbol if not char.isdigit()]).rstrip('CP')

def get_option_expiration_date(option_symbol):
    year = int('20' + option_symbol[len(option_symbol)-15:len(option_symbol)-13])
    month = int(option_symbol[len(option_symbol)-13:len(option_symbol)-11])
    day = int(option_symbol[len(option_symbol)-11:len(option_symbol)-9])
    
    return datetime(year, month, day)