from scipy.signal import argrelextrema

import math
import numpy as np
import pandas as pd
import os

def classification(df):
    size = int(os.getenv('RUNNUP'))

    df['min'] = df.iloc[argrelextrema(df.close.values, np.less_equal,
                    order=size)[0]]['close']
    df['max'] = df.iloc[argrelextrema(df.close.values, np.greater_equal,
                    order=size)[0]]['close']

    def label(row):
        if not math.isnan(row['max']):
            return 'sell'
        elif not math.isnan(row['min']):
            return 'buy'
        
        for i in range(5):
            j = i + 1
            if not math.isnan(row[f'min_{i}_next']):
                return 'buy'
            elif not math.isnan(row[f'min_{i}_past']):
                return 'buy'
            if not math.isnan(row[f'max_{i}_next']):
                return 'sell'
            elif not math.isnan(row[f'max_{i}_past']):
                return 'sell'
        
        return 'hold'
    
    for i in range(5):
        j = i + 1
        df[f'min_{i}_next'] = df['min'].shift(-j)
        df[f'min_{i}_past'] = df['min'].shift(j)
        df[f'max_{i}_next'] = df['max'].shift(-j)
        df[f'max_{i}_past'] = df['max'].shift(j)
    
    df['label'] = df.apply(label, axis=1)

    df.pop('min')
    df.pop('max')

    for i in range(5):
        df.pop(f'min_{i}_next')
        df.pop(f'min_{i}_past')
        df.pop(f'max_{i}_next')
        df.pop(f'max_{i}_past')

    return df