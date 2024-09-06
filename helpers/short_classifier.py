from helpers import features

import os
import numpy as np

def classification(df):
    time_window = int(os.getenv('TIME_WINDOW'))
    look_forward = int(os.getenv('LOOK_FORWARD'))

    for i in range(look_forward):
        j = i + 1
        df[f'next_close_{i}'] = df['close'].shift(-j)

    def next_close_trend(row):
        return features.trending(row, 'next_close', look_forward, False, False, False)

    df[f'next_close'] = df.apply(next_close_trend, axis=1)

    df = df[df['next_close'] < 2]
    df = df[df['next_close'] > -2]

    g = df[df['next_close'] > 0]['next_close']
    s = df[df['next_close'] < 0]['next_close']

    g_trend = g.mean() 
    s_trend = s.mean() 

    print(f'Growth {g_trend} Shrink {s_trend}')

    def label(row):
        # growth indicators
        growth = row['next_close'] > g_trend
        p_trend = row['close_trend'] > 0
        roc = row['roc_trend'] > 0
        bands = row['percent_b'] > 0.5
        green_candle = row['candle_bar'] < 0
        pvi = row['pvi_trend'] > 0 and abs(row['pvi_trend']) > abs(row['nvi_trend'])

        if growth and p_trend and roc and bands and green_candle and pvi:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < s_trend
        p_trend = row['close_trend'] < 0
        roc = row['roc_trend'] < 0
        bands = row['percent_b'] < 0.5
        red_candle = row['candle_bar'] > 0
        nvi = row['nvi_trend'] > 0 and abs(row['pvi_trend']) < abs(row['nvi_trend'])

        if shrink and p_trend and roc and red_candle and nvi:
            return 'sell' 
        
        return 'hold'

    df['label'] = df.apply(label, axis=1)

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])

    print(f'buy count: {buys} sell count: {sells} hold count: {holds}')

    for i in range(look_forward):
        j = i + 1
        df.pop(f'next_close_{i}')
    df.pop('next_close')

    return df

def label_to_int(row):
    if row == 'buy': return 0
    elif row == 'sell': return 1
    elif row == 'hold': return 2

def int_to_label(row):
    if row == 0: return 'Buy'
    elif row == 1: return 'Sell'
    elif row == 2: return 'Hold'