from src.helpers import features

import pandas as pd
import numpy as np

def classification(df):
    def label(row):
        if row['hour'] >= 19:
            return 'hold'

        up = (row['close'] < row['next_short_dist'] < row['next_large_dist']) and (row['percent_difference'] >= upd)
        pvi = row['pvi_short_trend'] > 0# and row['pvi_cross_over'] == True
        macd = row['macd_short_trend'] > 0# and row['macd_cross_over'] == True
        roc = row['roc_short_trend'] > 0# and row['roc_cross_over'] == True
        bands = row['upper_band_short_trend'] < 0 and row['upper_band_short_trend'] > 0
        squeeze = row['squeeze_on']
        hist = row['histogram'] > .2
        dip = row['min_short'] or row['min_long']

        if up and dip and sum([pvi, macd, roc, squeeze, bands, hist]) >= 2:
            return 'buy'

        down = (row['close'] > row['next_short_dist'] > row['next_large_dist']) and (row['percent_difference'] <= downd)
        nvi = row['nvi_short_trend'] > 0 and row['nvi_cross_over'] == True
        macd = row['macd_short_trend'] < 0# and row['macd_cross_below'] == True
        roc = row['roc_short_trend'] < 0# and row['roc_cross_below'] == True
        bands = row['upper_band_short_trend'] < 0 and row['upper_band_short_trend'] > 0
        hist = row['histogram'] < -.2
        dip = row['max_short'] or row['max_long']

        if down and dip and sum([nvi, macd, roc, bands, hist]) >= 2:
            return 'sell'

        return 'hold'

    df['next_short_dist'] = df['close'].shift(15)
    df['next_large_dist'] = df['close'].shift(15)
    df['percent_difference'] = ((df['next_large_dist'] - df['close']) / df['close'])

    upd = df[df['percent_difference'] > 0]['percent_difference'].mean()# + df[df['percent_difference'] > 0]['percent_difference'].std()
    downd = df[df['percent_difference'] < 0]['percent_difference'].mean()# + df[df['percent_difference'] < 0]['percent_difference'].std()

    df['label'] = df.apply(label, axis=1)

    df.pop('next_short_dist')
    df.pop('next_large_dist')
    df.pop('percent_difference')

    return df