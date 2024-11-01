from src.helpers import features

import pandas as pd
import numpy as np
import os

def classification(df):
    def label(row):
        pvi = row['pvi'] <= 1 and row['pvi'] - row['pvi__last'] >= 0
        roc = row['roc'] <= 0 and row['roc'] - row['roc__last'] >= 0
        macd = row['macd'] <= 0 and row['histogram'] > 0
        bb = row['percent_b'] <= .5
        close = row['close_short_trend'] < 0

        if pvi and roc and macd and bb and close:
            return 'buy'

        nvi = row['nvi'] <= 1 and row['nvi'] - row['nvi__last'] >= 0
        roc = row['roc'] >= 0 and row['roc'] - row['roc__last'] <= 0
        macd = row['macd'] >= 0 and row['histogram'] <= 0
        bb = row['percent_b'] >= .5
        close = row['close_short_trend'] > 0

        if nvi and roc and macd and bb and close:
            return 'sell'

        return 'hold'
    
    df['label'] = df.apply(label, axis=1)

    return df