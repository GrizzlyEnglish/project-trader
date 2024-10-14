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

        if close_runnup == 1 and row['close_short_trend'] < 0:
            return 'buy'
        elif close_runnup == -1 and row['close_short_trend'] > 0:
            return 'sell'
        
        return 'hold'

    for i in range(size):
        j = i + 1
        df[f'close_{i}_next'] = df['close'].shift(-j)

    df['label'] = df.apply(label, axis=1)

    for i in range(size):
        df.pop(f'close_{i}_next')

    return df