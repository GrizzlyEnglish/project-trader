from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    symbol = df.index[0][0]
    delta = float(os.getenv(f'{symbol}_DELTA'))
    ticks = int(os.getenv(f'{symbol}_TICKS'))

    date_trends = {}

    def label(row):
        day_trend = date_trends[row.name[1].strftime("%Y-%m-%d")]

        bars = day_trend['bars']
        post = bars.loc[row.name[1]:]['close']

        post_arr = post[1:ticks]

        if (post_arr > (row['close'] - delta)).all() and row['close_short_trend'] > 0:
            return 'buy'
        
        if (post_arr < (row['close'] + delta)).all() and row['close_short_trend'] < 0:
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