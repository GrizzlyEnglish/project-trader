from src.helpers import get_data, features, class_model
from datetime import timedelta

import joblib
import os
import numpy as np
import pandas as pd

class TrendingModel:

    def __init__(self, symbol, end_date, day_diff, neighbors, market_client) -> None:
        self.market_client = market_client
        self.symbol = symbol
        self.start = end_date - timedelta(days=day_diff)
        self.end = end_date
        self.n = neighbors
        self.model = None

        # attempt to load first otherwise build it
        self.file_path = f"../generated/{self.symbol}_{neighbors}.joblib" 
        if os.path.exists(self.file_path):
            self.model = joblib.load(self.file_path)

        if self.model == None:
            self.setup_bars()

    def setup_bars(self) -> None:
        self.bars = get_data.get_bars(self.symbol, self.end - timedelta(days=90), self.end, self.market_client)
        self.bars = features.feature_engineer_df(self.bars)
        self.classify()

    def set_params(self, n, p) -> None:
        self.n = n
        self.p = p

    def classify(self):
        df = self.bars
        symbol = df.index[0][0]

        date_trends = {}

        def label(row):
            delta = float(os.getenv(f'{symbol}_DELTA'))

            day_trend = date_trends[row.name[1].strftime("%Y-%m-%d")]

            bars = day_trend['bars']
            post = bars.loc[row.name[1]:]

            for index, r2 in post.iterrows(): 
                d = r2['close'] - row['close']

                if d > delta:
                    return 'buy'
                elif d < -delta:
                    return 'sell'

            return 'hold'

        dates = np.unique(df.index.get_level_values('timestamp').date)
        for dt in dates:
            dtstr = dt.strftime("%Y-%m-%d")
            day_bars = df.loc[(symbol, dtstr)]
            date_trends[dtstr] = {
                'bars': day_bars,
            }

        df['indicator'] = df.apply(features.my_indicator, axis=1)
        df['label'] = df.apply(label, axis=1)

    def generate_model(self) -> dict:
        if self.model != None:
            return self.model

        bars = self.bars[self.bars['indicator'] != 0]
        bars = self.bars[self.bars['label'] != 'hold']

        bars.pop('indicator')

        print(f'Buys {len(bars[bars["label"] == "buy"])} Sells {len(bars[bars["label"] == "sell"])}')

        self.model = class_model.create_model(self.symbol, bars, self.n)

        joblib.dump(self.model, self.file_path)

        return self.model