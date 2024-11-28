from src.helpers import get_data, features, class_model
from typing import Dict

import os
import numpy as np
import math

class TrendingModel:

    def __init__(self, symbol, market_client) -> None:
        self.market_client = market_client
        self.symbol = symbol
        self.bars = []

    def add_bars(self, bars) -> None:
        self.bars = bars

    def feature_engineer_bars(self) -> None:
        self.bars = features.feature_engineer_df(self.bars)

    def classify(self):
        df = self.bars
        symbol = df.index[0][0]
        ticks = int(os.getenv(f'TICKS'))

        date_trends = {}

        def label(row):
            day_trend = date_trends[row.name[1].strftime("%Y-%m-%d")]

            bars = day_trend['bars']
            post = bars.loc[row.name[1]:]

            post = post[1:ticks]

            if all(value >= row['close'] for value in post['open']) and all(value >= row['close'] for value in post['close']):
                return 'buy'
            
            if all(value <= row['close'] for value in post['open']) and all(value <= row['close'] for value in post['close']):
                return 'sell'

            return 'hold'

        dates = np.unique(df.index.get_level_values('timestamp').date)
        for dt in dates:
            dtstr = dt.strftime("%Y-%m-%d")
            day_bars = df.loc[(symbol, dtstr)]
            date_trends[dtstr] = {
                'bars': day_bars,
            }

        df['label'] = df.apply(label, axis=1)

    def generate_model(self) -> dict:
        return class_model.create_model(self.symbol, self.bars)