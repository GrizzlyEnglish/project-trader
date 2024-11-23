from src.helpers import features

import pandas as pd
import numpy as np
import os
import math

def classification(df):
    symbol = df.index[0][0]
    ticks = int(os.getenv(f'TICKS'))

    date_trends = {}

    def label(row):
        day_trend = date_trends[row.name[1].strftime("%Y-%m-%d")]

        bars = day_trend['bars']
        post = bars.loc[row.name[1]:]

        post = post[1:ticks]
        post_close = post['close']

        greens = len(post[post['candle_bar'] > 0])
        reds = len(post[post['candle_bar'] < 0])

        half_ticks = math.ceil(ticks/2)

        if greens >= half_ticks and (post_close > (row['close'] - 1)).all():
            return 'buy'
        
        if reds >= half_ticks and (post_close < (row['close'] + 1)).all():
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

    return df