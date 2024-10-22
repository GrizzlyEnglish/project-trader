from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    size = int(os.getenv('RUNNUP'))

    def label(row):
        if row['hour'] < 14 or row['hour'] >= 19:
            return 'hold'

        close_runnup = features.runnup(row, 'close', size, 'next', True, False, False)

        if close_runnup == 1 and row['min_short'] and row['diff'] >= up_diff:
            return 'buy'
        elif close_runnup == -1 and row['max_short'] and row['diff'] <= down_diff:
            return 'sell'
        
        return 'hold'

    for i in range(size):
        j = i + 1
        df[f'close_{i}_next'] = df['close'].shift(-j)

    df['diff'] = df[f'close_{size-1}_next'] - df['close']

    up_diff = df[df['diff'] > 0]['diff'].mean()# + df[df['diff'] > 0]['diff'].std()
    down_diff = df[df['diff'] < 0]['diff'].mean()# - df[df['diff'] > 0]['diff'].std()

    df['label'] = df.apply(label, axis=1)

    for i in range(size):
        df.pop(f'close_{i}_next')
    
    df.pop('diff')

    return df