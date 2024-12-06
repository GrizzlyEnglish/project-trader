from src.helpers import get_data, features, class_model
from datetime import timedelta

import joblib
import os
import numpy as np
import pandas as pd

class TrendingModel:

    def __init__(self, symbol, end_date, day_diff, neighbors, market_client, force_build = False) -> None:
        self.market_client = market_client
        self.symbol = symbol
        self.start = end_date - timedelta(days=day_diff)
        self.end = end_date
        self.n = neighbors
        self.model = None

        # attempt to load first otherwise build it
        self.file_path = f"../generated/{self.symbol}_{neighbors}.joblib" 
        if not force_build and os.path.exists(self.file_path):
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

        def set_post_trend(row):
            delta = float(os.getenv(f'{symbol}_DELTA'))

            day_trend = date_trends[row.name[1].strftime("%Y-%m-%d")]

            bars = day_trend['bars']
            post = bars.loc[row.name[1]:]

            slope = features.slope(post['close'])
            return 0 if slope == 0 else slope[0]
        
        def label(row):
            if row['post_trend'] > up_pt:
                return 'buy'
            if row['post_trend'] < down_pt:
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
        df['post_trend'] = df.apply(set_post_trend, axis=1)

        up_pt = df[df['post_trend'] > 0]['post_trend'].mean() + df[df['post_trend'] > 0]['post_trend'].std()
        down_pt = df[df['post_trend'] < 0]['post_trend'].mean() - df[df['post_trend'] < 0]['post_trend'].std()

        df['label'] = df.apply(label, axis=1)

        df.pop('post_trend')

    def generate_model(self) -> dict:
        if self.model != None:
            return self.model

        bars = self.bars.copy()
        #bars = bars[bars['indicator'] != 0]
        bars = bars[bars['label'] != 'hold']

        bars.pop('indicator')

        print(f'Buys {len(bars[bars["label"] == "buy"])} Sells {len(bars[bars["label"] == "sell"])}')

        self.model = class_model.create_model(self.symbol, bars, self.n)

        joblib.dump(self.model, self.file_path)

        return self.model