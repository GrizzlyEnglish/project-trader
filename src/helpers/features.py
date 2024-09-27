from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote, CandlePart
from sklearn.preprocessing import MinMaxScaler

import numpy as np
import math
import os
import pandas as pd

small_window = 50
large_window = 200
length_KC = 20
mult_KC = 1.5

def trending(df, label, amt, prepend=False, postpend=False, reverse=True):
    arr = []

    if prepend:
        arr.append(df[label])

    for i in range(amt):
        arr.append(df[f'{label}_{i}'])

    if postpend:
        arr.append(df[label])

    if reverse:
        arr.reverse()

    return slope(arr)

def slope(arr):
    if len(arr) <= 1:
        return 0
    arr = np.vstack(arr)
    poly_coeffs = np.polyfit(np.arange(len(arr)), np.vstack(arr), 1)
    poly_coeffs[np.isnan(poly_coeffs)] = 0  # possible speed-up: insert zeros where needed
    return poly_coeffs[0, :]  # slope only

def feature_engineer_df(df, look_back):
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

    def get_hour(row):
        idx = row.name[1]
        return idx.hour

    df['hour'] = df.apply(get_hour, axis=1)

    def get_minutes(row):
        idx = row.name[1]
        return idx.minute

    df['minutes'] = df.apply(get_minutes, axis=1)

    def in_time(row):
        return row['hour'] >= 12 and row['hour'] < 19

    df['in_time'] = df.apply(in_time, axis=1)

    # candle sticks
    df['candle_bar'] = df['open'] - df['close']
    df['candle_lines'] = df['high'] - df['low']

    df = moving_average(df, quotes)

    df = macd(df, quotes)

    df = rate_of_change(df, quotes)

    df = obv(df, quotes)

    df = rsi(df, quotes)

    df = vortex_indicator(df, quotes)

    df = bands(df, quotes)

    df = smi(df, quotes)

    df = trends(df, look_back)

    df = mfi(df, quotes)

    df = truerange(df)

    df = squeeze(df)

    return df

def drop_prices(df, look_back):
    for i in range(look_back):
        df.pop(f'close_{i}')
        df.pop(f'pvi_{i}')
        df.pop(f'nvi_{i}')
        df.pop(f'smi_{i}')
        df.pop(f'roc_{i}')
        df.pop(f'macd_{i}')
        df.pop(f'histogram_{i}')
        df.pop(f'percent_b_{i}')

    return df

def trends(df, look_back):
    col_names = ['close', 'pvi', 'nvi', 'smi', 'macd', 'roc', 'histogram', 'percent_b', 'height']
    for i in range(look_back):
        j = i + 1
        df2 = df[col_names]
        df2 = df2.add_suffix(f'_{i}')
        df2 = df2.shift(j)
        df = pd.concat([df, df2], axis=1)

    for col_name in col_names:
        df[f'{col_name}_trend'] = trending(df, col_name, look_back, True, False)

    return df

def truerange(df):
    # calculate true range
    df['tr0'] = abs(df["high"] - df["low"])
    df['tr1'] = abs(df["high"] - df["close"].shift())
    df['tr2'] = abs(df["low"] - df["close"].shift())
    df['tr'] = df[['tr0', 'tr1', 'tr2']].max(axis=1)

    # calculate KC
    m_avg = df['close'].rolling(window=length_KC).mean()
    range_ma = df['tr'].rolling(window=length_KC).mean()
    df['upper_KC'] = m_avg + range_ma * mult_KC
    df['lower_KC'] = m_avg - range_ma * mult_KC

    return df

def squeeze(df):
    df['squeeze_on'] = (df['lower_band'] > df['lower_KC']) & (df['upper_band'] < df['upper_KC'])
    df['squeeze_off'] = (df['lower_band'] < df['lower_KC']) & (df['upper_band'] > df['upper_KC'])

    return df

def mfi(df, quotes):
    results = indicators.get_mfi(quotes, 14)
    df.loc[:, 'mfi'] = [r.mfi for r in results]

    return df

def bands(df, quotes):
    results = indicators.get_bollinger_bands(quotes, 20, 2)

    df.loc[:, 'percent_b'] = [r.percent_b for r in results]
    df.loc[:, 'width'] = [r.width for r in results]
    df.loc[:, 'upper_band'] = [r.upper_band for r in results]
    df.loc[:, 'lower_band'] = [r.lower_band for r in results]
    df.loc[:, 'z_score'] = [r.z_score for r in results]

    df['height'] = df['upper_band'] - df['lower_band']

    return df

def vortex_indicator(df, quotes):
    results = indicators.get_vortex(quotes, 14)

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
