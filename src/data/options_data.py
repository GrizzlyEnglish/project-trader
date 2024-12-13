from alpaca.data.historical.option import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.requests import OptionSnapshotRequest
from datetime import datetime, timezone, timedelta
from src.helpers import options, features

import math
import pandas as pd

class OptionData:

    def __init__(self, underlying_symbol, current_time, c_or_p, strike_price, option_client) -> None:
        self.option_client = option_client
        self.underlying_symbol = underlying_symbol
        self.is_polygon = False
        self.dte = current_time
        self.strike = self.determine_strike(strike_price, current_time, self.dte, c_or_p)
        self.symbol = options.create_option_symbol(underlying_symbol, self.dte, c_or_p, self.strike)

    def determine_strike(self, strike, current_time, dte, c_or_p) -> int:
        eob = dte.replace(hour=18)
        dst = math.floor((eob - current_time).total_seconds() / 3600)
        if dst < 2:
            self.dte = self.dte + timedelta(days=1)
            if self.dte.weekday() == 5:
                self.dte = self.dte + timedelta(days=2)
            dst = 1
        else:
            dst = 6 - dst
        new_strike = math.floor(strike - dst) if c_or_p == 'C' else math.ceil(strike + dst)
        print(f'{dst} with {eob-current_time} {c_or_p} changing {strike} to {new_strike}')
        strike = new_strike
        return strike

    def set_symbol(self, symbol) -> None:
        self.symbol = symbol

    def set_polygon(self, is_polygon) -> None:
        self.is_polygon = is_polygon

    def get_bars(self, start, end):
        bars = []
        bars = self.get_alpaca_bars(start, end)
        if bars.empty:
            return bars
        if len(bars) < 20:
            return pd.DataFrame()
        return features.feature_engineer_options(bars)

    def get_alpaca_bars(self, start, end):
        bars = self.option_client.get_option_bars(OptionBarsRequest(symbol_or_symbols=self.symbol, start=start, end=end, timeframe=TimeFrame(1, TimeFrameUnit.Minute)))
        return bars.df

    def get_option_snap_shot(self):
        last_quote = self.option_client.get_option_snapshot(OptionSnapshotRequest(symbol_or_symbols=self.symbol))
        return last_quote[self.symbol]