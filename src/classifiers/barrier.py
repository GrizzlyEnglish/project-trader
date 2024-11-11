from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    trend = int(os.getenv('TREND'))

    def label(row):
        if row['indicator'] == 0:
            return 'hold'

        b = row['close'] - 1
        close_runnup = features.runnup(row, b, 'close', trend, 'next', True, False, False)
        if close_runnup == 1 and row['indicator'] == 1:
            return 'buy'

        b = row['close'] + 1
        close_runnup = features.runnup(row, b, 'close', trend, 'next', True, False, False)
        if close_runnup == -1 and row['indicator'] == -1:
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