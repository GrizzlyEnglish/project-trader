from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    size = int(os.getenv('RUNNUP'))

    def label(row):
        if row['hour'] >= 19:
            return 'hold'
        
        if row['next_change_trend'] > up_trend:
            return 'buy'
        elif row['next_change_trend'] < down_trend:
            return 'sell'
        
        return 'hold'
    
    for i in range(size):
        j = i + 1
        df2 = df[['change', 'close']]
        df2 = df2.add_suffix(f'_{i}_next')
        df2 = df2.shift(-j)
        df = pd.concat([df, df2], axis=1)

    df['next_change_trend'] = features.trending(df, 'change', size, 'next', False, True, False)

    u_arr = df[df['next_change_trend'] > 0]['next_change_trend']
    d_arr = df[df['next_change_trend'] < 0]['next_change_trend']
    up_trend = u_arr.mean()# + u_arr.std()
    down_trend = d_arr.mean()# - d_arr.std()

    df['label'] = df.apply(label, axis=1)

    for i in range(size):
        df.pop(f'change_{i}_next')
        df.pop(f'close_{i}_next')

    df.pop('next_change_trend')

    return df