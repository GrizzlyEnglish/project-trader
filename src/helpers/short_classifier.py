from src.helpers import features

import math
import numpy as np
import pandas as pd

def classification(df, look_forward):
    def next_close_perc_diff(row):
        if not math.isnan(row[f'close_next_{look_forward-1}']):
            return features.get_percentage_diff(row['close'], row[f'close_next_{look_forward-1}'], False)
        else:
            return 0

    def label(row):
        it = row['in_time']
        # growth indicators
        growth = row['next_close'] > g_trend
        diff = row['next_close_perc_diff'] > gpd_trend

        if it and growth and diff:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < s_trend
        diff = row['next_close_perc_diff'] < spd_trend

        if it and shrink and diff:
            return 'sell' 
        
        return 'hold'
    
    def in_time(row):
        return row.name[1].hour >= 12 and row.name[1].hour < 19

    # Setup next close on rows
    for i in range(look_forward):
        j = i + 1
        df2 = df[['close']]
        df2 = df2.add_suffix(f'_next_{i}')
        df2 = df2.shift(-j)
        df = pd.concat([df, df2], axis=1)

    # Setup extra columns for determing label
    df[f'next_close'] = features.trending(df, 'close_next', look_forward, False, False, False)
    df[f'in_time'] = df.apply(in_time, axis=1)
    df[f'next_close_perc_diff'] = df.apply(next_close_perc_diff, axis=1)

    # For getting the trends use only in time
    df_it = df[df['in_time'] == True]

    g = df_it[df_it['next_close'] > 0]['next_close']
    s = df_it[df_it['next_close'] < 0]['next_close']

    g_trend = g.mean() + g.std()
    s_trend = s.mean() - s.std()

    gpd = df_it[df_it['next_close_perc_diff'] > 0]['next_close_perc_diff']
    spd = df_it[df_it['next_close_perc_diff'] < 0]['next_close_perc_diff']
    gpd_trend = gpd.mean() + gpd.std()
    spd_trend = spd.mean() - spd.std()

    df['label'] = df.apply(label, axis=1)

    for i in range(look_forward):
        j = i + 1
        df.pop(f'close_next_{i}')

    df.pop('next_close')
    df.pop('next_close_perc_diff')
    df.pop('in_time')

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])
    print(f'short buy count: {buys} sell count: {sells} hold count: {holds}')
    print(f'Perc diff {gpd_trend} Shrink {spd_trend}')
    print(f'Growth {g_trend} Shrink {s_trend}')

    return df, gpd_trend, spd_trend