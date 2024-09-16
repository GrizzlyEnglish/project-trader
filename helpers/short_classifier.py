from helpers import features

import math
import numpy as np

def classification(df, look_forward):
    for i in range(look_forward):
        j = i + 1
        df[f'next_close_{i}'] = df['close'].shift(-j)

    def next_close_trend(row):
        return features.trending(row, 'next_close', look_forward, False, False, False)

    df[f'next_close'] = df.apply(next_close_trend, axis=1)

    g = df[df['next_close'] > 0]['next_close']
    s = df[df['next_close'] < 0]['next_close']

    g_trend = g.mean() + g.std()
    s_trend = s.mean() - s.std()

    print(f'Growth {g_trend} Shrink {s_trend}')

    def next_close_perc_diff(row):
        if not math.isnan(row[f'next_close_{i}']):
            return features.get_percentage_diff(row['close'], row[f'next_close_{i}'], False)
        else:
            return 0

    df[f'next_close_perc_diff'] = df.apply(next_close_perc_diff, axis=1)

    gpd = df[df['next_close_perc_diff'] > 0]['next_close_perc_diff']
    spd = df[df['next_close_perc_diff'] < 0]['next_close_perc_diff']
    gpd_trend = gpd.mean() + gpd.std()
    spd_trend = spd.mean() - spd.std()

    print(f'Perc diff {gpd_trend} Shrink {spd_trend}')

    def label(row):
        # growth indicators
        growth = row['next_close'] > g_trend
        diff = row['next_close_perc_diff'] > gpd_trend
        #p_trend = row['close_trend'] > 0
        #roc = row['roc_trend'] > 0
        #bands = row['percent_b'] > 0.5
        #green_candle = row['candle_bar'] < 0
        #pvi = row['pvi_trend'] > 0 and abs(row['pvi_trend']) > abs(row['nvi_trend'])

        if growth and diff:# and p_trend and roc and bands and green_candle and pvi:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < s_trend
        diff = row['next_close_perc_diff'] < spd_trend
        #p_trend = row['close_trend'] < 0
        #roc = row['roc_trend'] < 0
        #bands = row['percent_b'] < 0.5
        #red_candle = row['candle_bar'] > 0
        #nvi = row['nvi_trend'] > 0 and abs(row['pvi_trend']) < abs(row['nvi_trend'])

        if shrink and diff:# and p_trend and roc and red_candle and nvi:
            return 'sell' 
        
        return 'hold'

    df['label'] = df.apply(label, axis=1)

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])

    print(f'short buy count: {buys} sell count: {sells} hold count: {holds}')

    for i in range(look_forward):
        j = i + 1
        df.pop(f'next_close_{i}')

    df.pop('next_close')
    df.pop('next_close_perc_diff')

    return df