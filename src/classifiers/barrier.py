from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    size = int(os.getenv('RUNNUP'))

    def label(row):
        if row['hour'] >= 19:
            return 'hold'

        close_runnup = features.runnup(row, 'close', size, 'next', True, False, False)

        if close_runnup == 1 and row['next_close_diff'] > udiff:
            return 'buy'
        elif close_runnup == -1 and row['next_close_diff'] < ddiff:
            return 'sell'
        
        return 'hold'

    for i in range(size):
        j = i + 1
        df[f'close_{i}_next'] = df['close'].shift(-j)

    df['next_close_diff'] = df[f'close_{size-1}_next'] - df['close']

    udiff = df[df['next_close_diff'] > 0]['next_close_diff'].mean()
    ddiff = df[df['next_close_diff'] < 0]['next_close_diff'].mean()

    df['label'] = df.apply(label, axis=1)

    for i in range(size):
        df.pop(f'close_{i}_next')

    df.pop('next_close_diff')

    return df