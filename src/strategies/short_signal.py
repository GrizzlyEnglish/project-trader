from src.helpers import get_data, features, class_model
from typing import Tuple

import os

class Short:

    def __init__(self, symbol, market_client) -> None:
        self.bars = []
        self.positions = []
        self.symbol = symbol
        self.market_client = market_client
        self.model = {}

    def add_bars(self, bars) -> None:
        self.bars = bars

    def add_model(self, model) -> None:
        self.model = model

    def add_positions(self, positions) -> None:
        self.positions = positions

    def signal(self) -> Tuple[bool, str]:
        bar = self.bars[-1:]
        indicator = features.my_indicator(bar.iloc[0])
        buy_amount = int(os.getenv('BUY_AMOUNT'))

        if indicator == 0:
            return False, 'hold', 0

        has_open_option = next((cp for cp in self.positions if self.symbol in cp.symbol), None) != None
        if has_open_option:
            return False, 'hold', 0

        signal = class_model.classify(self.model, self.bars)

        print(f'Signal {signal} indicator {indicator}')

        if indicator == 1 and signal != 'sell':
            qty = buy_amount*2 if signal == 'buy' else buy_amount
            return True, 'buy', qty
        elif indicator == -1 and signal != 'buy':
            qty = buy_amount*2 if signal == 'sell' else buy_amount
            return True, 'sell', qty
        else:
            return False, 'hold', 0

