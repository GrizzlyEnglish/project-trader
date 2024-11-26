from src.helpers import get_data, features, class_model
from typing import Tuple

import numpy as np

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

        if indicator == 0:
            return False, 'hold'
        elif indicator == 1:
            return True, 'buy'
        else:
            return True, 'sell'

        has_open_option = next((cp for cp in self.positions if self.symbol in cp.symbol), None) != None
        if has_open_option:
            return False, 'hold'

        signal = class_model.classify(self.model, self.bars)

        print(f'Signal {signal} indicator {indicator}')

        if signal == 'buy' and indicator == 1 or signal == 'sell' and indicator == -1:
            return True, signal

        return False, 'hold'

