from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote, CandlePart

import numpy as np
import math

small_window = 50
large_window = 200

def drop_prices(df):
    # Drop price based colums
    df.pop('open')
    df.pop('high')
    df.pop('low')
    df.pop('close')

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

    #shift
    #df['prev_macd'] = df['macd'].shift(1)
    #df['prev_rsi'] = df['rsi'].shift(1)
    #df['prev_pvi'] = df['pvi'].shift(1)
    #df['prev_nvi'] = df['nvi'].shift(1)

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
    #df.loc[:, 'kama'] = [r.kama for r in results]

    return df

def macd(df, quotes):
    results = indicators.get_macd(quotes, 12, 26, 9)

    df.loc[:, 'macd'] = [r.macd for r in results]
    df.loc[:, 'signal'] = [r.signal for r in results]
    #df.loc[:, 'fast_ema'] = [r.fast_ema for r in results]
    #df.loc[:, 'slow_ema'] = [r.slow_ema for r in results]
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
    df['shifted_close'] = df['close'].shift(-4)
    df['diff'] = df['close'] - df['shifted_close']

    s_diff = ((df[df['diff'] < 0]['diff'].mean() + df[df['diff'] < 0]['diff'].max()) / 2)
    g_diff = ((df[df['diff'] > 0]['diff'].mean() + df[df['diff'] > 0]['diff'].min()) / 2)

    def label(row):
        if math.isnan(row['shifted_close']): 
            return None
        
        shifted_diff = row['diff']

        growth = shifted_diff > g_diff
        shrink = shifted_diff < s_diff

        if growth and (row['pvi'] > row['nvi']) and row['macd'] > 0 and row['z_score'] > 1 and row['roc'] > 0.5 and row['percent_b'] >= .8:
            return 'buy' 
        elif shrink and (row['pvi'] < row['nvi']) and row['macd'] < 0 and row['z_score'] < -1 and row['roc'] < -0.5 and row['percent_b'] <= .20:
            return 'sell' 
        else:
            return 'hold'

    df['label'] = df.apply(label, axis=1)

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])

    print(f'buy count: {buys} sell count: {sells} hold count: {holds}')

    df.pop('shifted_close')
    df.pop('diff')

    return df

def label_to_int(row):
    if row == 'buy': return 0
    elif row == 'sell': return 1
    elif row == 'hold': return 2

def int_to_label(row):
    if row == 0: return 'Buy'
    elif row == 1: return 'Sell'
    elif row == 2: return 'Hold'