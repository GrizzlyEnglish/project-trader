from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    trend = int(os.getenv('TREND'))

    def label(row):
        if row['next_close_diff'] >= 1 and row['indicator'] == 1:
            return 'buy'
        elif row['next_close_diff'] <= -1 and row['indicator'] == -1:
            return 'sell'
        
        return 'hold'

    # close diff
    df[f'close_last_next'] = df['close'].shift(-trend)
    df['next_close_diff'] = df[f'close_last_next'] - df['close']

    df['label'] = df.apply(label, axis=1)

    df.pop('close_last_next')
    df.pop('next_close_diff')

    return df