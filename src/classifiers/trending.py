from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    trend = int(os.getenv('TREND'))

    def label(row):
        if row['hour'] >= 19:
            return 'hold'

        if row['next_close_trend'] >= up_trend and row['close_short_trend'] < 0:
            return 'buy'
        elif row['next_close_trend'] <= down_trend and row['close_short_trend'] > 0:
            return 'sell'
        
        return 'hold'

    for i in range(trend):
        j = i + 1
        df2 = df[['close']]
        df2 = df2.add_suffix(f'_{i}_next_close')
        df2 = df2.shift(-j)
        df = pd.concat([df, df2], axis=1)
    df['next_close_trend'] = features.trending(df, 'close', trend, 'next_close', False, True, False)

    u_arr = df[df['next_close_trend'] > 0]['next_close_trend']
    d_arr = df[df['next_close_trend'] < 0]['next_close_trend']
    up_trend = u_arr.mean() + u_arr.std()
    down_trend = d_arr.mean() - d_arr.std()

    df['label'] = df.apply(label, axis=1)

    for i in range(trend):
        df.pop(f'close_{i}_next_close')

    df.pop('next_close_trend')

    return df