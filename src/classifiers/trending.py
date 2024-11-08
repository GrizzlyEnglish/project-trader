from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    trend = int(os.getenv('TREND'))

    def label(row):
        if row['hour'] >= 19:
            return 'hold'

        close_runnup = features.runnup(row, 'close', trend, 'next', True, False, False)

        if row['next_close_diff'] >= uclosediff and close_runnup == 1:
            return 'buy'
        elif row['next_close_diff'] <= dclosediff and close_runnup == -1:
            return 'sell'
        
        return 'hold'

    for i in range(trend):
        j = i + 1
        df2 = df[['close']]
        df2 = df2.add_suffix(f'_{i}_next')
        df2 = df2.shift(-j)
        df = pd.concat([df, df2], axis=1)

    # close diff
    df[f'close_last_next'] = df['close'].shift(-trend)
    df['next_close_diff'] = df[f'close_last_next'] - df['close']
    up = df[df['next_close_diff'] > 0]['next_close_diff']
    down = df[df['next_close_diff'] < 0]['next_close_diff']
    uclosediff = up.mean() + up.std()
    dclosediff = down.mean() - down.std()

    df['label'] = df.apply(label, axis=1)

    for i in range(trend):
        df.pop(f'close_{i}_next')

    df.pop('close_last_next')
    df.pop('next_close_diff')

    return df