from alpaca.data.historical.option import OptionBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.requests import OptionSnapshotRequest
from datetime import datetime, timezone
from src.helpers import options

import math
import pandas as pd

class OptionData:

    def __init__(self, underlying_symbol, dte, c_or_p, strike_price, option_client, polygon_client) -> None:
        self.option_client = option_client
        self.polygon_client = polygon_client
        self.underlying_symbol = underlying_symbol
        self.is_polygon = False
        self.strike = self.determine_strike(strike_price, dte, c_or_p)
        self.symbol = options.create_option_symbol(underlying_symbol, dte, c_or_p, self.strike)

    def determine_strike(self, strike, dte, c_or_p) -> int:
        oob = dte.replace(hour=9)
        dst = ((dte - oob).total_seconds() / 3600) / 2
        strike = math.floor(strike - dst) if c_or_p == 'C' else math.ceil(strike + dst)
        return strike

    def set_symbol(self, symbol) -> None:
        self.symbol = symbol

    def set_polygon(self, is_polygon) -> None:
        self.is_polygon = is_polygon

    def get_bars(self, start, end):
        if self.is_polygon:
            return self.get_polygon_bars(start, end)
        else:
            return self.get_alpaca_bars(start, end)

    def get_polygon_bars(self, start, end):
        bars = self.polygon_client.list_aggs(ticker=f'O:{self.symbol}', multiplier=1, timespan="minute", from_=start, to=end)
        bars = list(bars)
        bars = pd.DataFrame(bars)
        bars['timestamp'] = bars['timestamp'].apply(lambda x: datetime.fromtimestamp(x / 1000, timezone.utc))
        bars['trade_count'] = bars['transactions']
        bars.set_index([pd.Index([self.symbol] * len(bars)), bars['timestamp']], inplace=True) 
        bars.index.names = ['symbol', 'timestamp']
        bars.drop(columns=['timestamp', 'otc', 'transactions'], inplace=True)
        return bars

    def get_alpaca_bars(self, start, end):
        bars = self.option_client.get_option_bars(OptionBarsRequest(symbol_or_symbols=self.symbol, start=start, end=end, timeframe=TimeFrame(1, TimeFrameUnit.Minute)))
        return bars.df

    def get_option_snap_shot(self):
        last_quote = self.option_client.get_option_snapshot(OptionSnapshotRequest(symbol_or_symbols=self.symbol))
        return last_quote[self.symbol]