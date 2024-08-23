from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote, CandlePart

import numpy as np
import math

small_window = 50
large_window = 200

def trending(row, label, amt, prepend = False, postpend = False):
    arr = []

    if prepend:
        arr.append(row[label])

    for i in range(amt):
        arr.append(row[f'{label}_{i}'])

    if postpend:
        arr.append(row[label])
    
    if all(arr[i] <= arr[i+1] for i in range(len(arr) - 1)):
        return 1
    elif all(arr[i] >= arr[i+1] for i in range(len(arr) - 1)):
        return -1
    else:
        return 0

def drop_prices(df):
    # Drop price based colums
    #df.pop('open')
    #df.pop('high')
    #df.pop('low')
    #df.pop('close')
    #df.pop('vwap')

    return df

def feature_engineer_df(df):
    bars_i = df.reset_index()
    quotes = [ 
        Quote(date, open, high, low, close, volume) 
            for date, open, high, low, close, volume 
            in zip(bars_i['timestamp'],
                bars_i['open'], 
                bars_i['high'], 
                bars_i['low'],
                bars_i['close'], 
                bars_i['volume'], strict=True)]

    df.loc[:, 'change'] = df['close'].diff()

    df = moving_average(df, quotes)

    df = macd(df, quotes)

    df = rate_of_change(df, quotes)

    df = obv(df, quotes)

    df = rsi(df, quotes)

    df = vortex_indicator(df, quotes)

    df = bands(df, quotes)

    df = smi(df, quotes)

    return df

def bands(df, quotes):
    results = indicators.get_bollinger_bands(quotes, 20, 2)

    df.loc[:, 'percent_b'] = [r.percent_b for r in results]
    df.loc[:, 'width'] = [r.width for r in results]
    df.loc[:, 'z_score'] = [r.z_score for r in results]

    return df

def vortex_indicator(df, quotes):
    results = indicators.get_vortex(quotes, 14);

    df.loc[:, 'pvi'] = [r.pvi for r in results]
    df.loc[:, 'nvi'] = [r.nvi for r in results]

    return df

def moving_average(df, quotes):
    results = indicators.get_kama(quotes, 10, small_window, large_window)

    df.loc[:, 'efficiency_ratio'] = [r.efficiency_ratio for r in results]
    df.loc[:, 'kama'] = [r.kama for r in results]

    return df

def macd(df, quotes):
    results = indicators.get_macd(quotes, 12, 26, 9)

    df.loc[:, 'macd'] = [r.macd for r in results]
    df.loc[:, 'signal'] = [r.signal for r in results]
    df.loc[:, 'fast_ema'] = [r.fast_ema for r in results]
    df.loc[:, 'slow_ema'] = [r.slow_ema for r in results]
    df.loc[:, 'histogram'] = [r.histogram for r in results]

    return df

def rate_of_change(df, quotes): 
    results = indicators.get_roc(quotes, 14)

    df.loc[:, 'roc'] = [r.roc for r in results]
    df.loc[:, 'roc_momentum'] = [r.momentum for r in results]

    return df

def obv(df, quotes):
    results = indicators.get_obv(quotes)
    df.loc[:, 'obv'] = [r.obv for r in results]
    return df

def rsi(df, quotes):
    results = indicators.get_rsi(quotes, 14)
    df.loc[:, 'rsi'] = [r.rsi for r in results]
    
    return df

def smi(df, quotes):
    results = indicators.get_smi(quotes, 10, 3, 3, 10)
    df.loc[:, 'smi'] = [r.smi for r in results]

    return df


def get_percentage_diff(previous, current, round_value=True):
    try:
        absolute_diff = current - previous
        average_value = (current + previous) / 2
        percentage = (absolute_diff / average_value) * 100.0

        if round_value:
            percentage = round(percentage)
        
        return percentage
    except ZeroDivisionError:
        return float('inf')  # Infinity

def classification(df):
    df[f'next_close'] = df['close'].shift(-20)

    def label(row):
        # growth indicators
        growth = row['next_close'] > row['close'] 
        z_score = row['z_score'] > 1
        perb = row['percent_b'] >= 0.8
        pvi = row['pvi'] > 1 and row['pvi'] >= row['nvi']
        roc = row['roc'] > 0
        macd = row['histogram'] > 0 

        if growth and pvi and z_score and perb and roc and macd:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < row['close']
        z_score = row['z_score'] < -1
        perb = row['percent_b'] <= 0.2
        nvi = row['nvi'] > 1  and row['pvi'] <= row['nvi']
        roc = row['roc'] < 0
        macd = row['histogram'] < 0

        if shrink and nvi and z_score and perb and nvi and roc and macd:
            return 'sell' 
        
        # dunno hold it
        return 'hold'

    df['label'] = df.apply(label, axis=1)

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])

    print(f'buy count: {buys} sell count: {sells} hold count: {holds}')

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