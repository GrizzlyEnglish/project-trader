from scipy.signal import argrelextrema

import math
import numpy as np
import pandas as pd

def classification(df, look_forward):
    n = look_forward

    df['min'] = df.iloc[argrelextrema(df.close.values, np.less_equal,
                    order=n)[0]]['close']
    df['max'] = df.iloc[argrelextrema(df.close.values, np.greater_equal,
                    order=n)[0]]['close']

    def label(row):
        if not math.isnan(row['max']):
            return 'sell'
        elif not math.isnan(row['min']):
            return 'buy'
        
        return 'hold'
    
    df['label'] = df.apply(label, axis=1)

    df.pop('min')
    df.pop('max')

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])
    print(f'short buy count: {buys} sell count: {sells} hold count: {holds}')

    return df, 0, 0