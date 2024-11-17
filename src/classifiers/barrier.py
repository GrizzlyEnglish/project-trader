from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    symbol = df.index[0][0]
    trend = int(os.getenv(f'{symbol}_TREND'))
    delta = float(os.getenv(f'{symbol}_DELTA'))

    def label(row):
        if row['hour'] >= 19:
            return 'hold'

        arr = features.trending_arr(row, 'close', trend, 'next', True, False, False)
        arr = np.array(arr)

        b = row['close'] - delta
        close_runnup = features.barrier(arr, b)
        if close_runnup == 1:
            return 'buy'

        b = row['close'] + delta
        close_runnup = features.barrier(arr, b)
        if close_runnup == -1:
            return 'sell'
        
        return 'hold'
    
    for i in range(trend):
        j = i + 1
        df2 = df[['close']]
        df2 = df2.add_suffix(f'_{i}_next')
        df2 = df2.shift(-j)
        df = pd.concat([df, df2], axis=1)

    df['label'] = df.apply(label, axis=1)

    for i in range(trend):
        df.pop(f'close_{i}_next')

    return df