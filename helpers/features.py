from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote, CandlePart
from sklearn.preprocessing import MinMaxScaler

import numpy as np
import math
import statistics

small_window = 50
large_window = 200

def trending(row, label, amt, prepend = False, postpend = False, reverse = True):
    arr = []

    if prepend:
        arr.append(row[label])

    for i in range(amt):
        arr.append(row[f'{label}_{i}'])

    if postpend:
        arr.append(row[label])

    if reverse:
        arr.reverse()

    if any(math.isnan(x) for x in arr):
        return 0

    coeffs = np.polyfit(range(len(arr)), arr, 1)
    slope = coeffs[-2]
    return float(slope)

    #return sum([0]+[(arr[n+1]-arr[n])/arr[n]*100 if arr[n] else 0 for n in range(len(arr)-2)])

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

    df = trends(df)

    return df

def drop_prices(df):
    # Drop price based colums
    trend_shift = 3

    for i in range(trend_shift):
        df.pop(f'close_{i}')
        df.pop(f'pvi_{i}')
        df.pop(f'nvi_{i}')
        df.pop(f'smi_{i}')
        df.pop(f'roc_{i}')
        df.pop(f'macd_{i}')
        df.pop(f'histogram_{i}')
        df.pop(f'percent_b_{i}')

    return df

def trends(df):
    trend_shift = 3

    for i in range(trend_shift):
        j = i + 1
        df[f'close_{i}'] = df['close'].shift(j)
        df[f'pvi_{i}'] = df['pvi'].shift(j)
        df[f'nvi_{i}'] = df['nvi'].shift(j)
        df[f'smi_{i}'] = df['smi'].shift(j)
        df[f'roc_{i}'] = df['roc'].shift(j)
        df[f'macd_{i}'] = df['macd'].shift(j)
        df[f'histogram_{i}'] = df['histogram'].shift(j)
        df[f'percent_b_{i}'] = df['percent_b'].shift(j)

    def close_trend(row):
        return trending(row, 'close', trend_shift, True, False)

    def pvi_trend(row):
        return trending(row, 'pvi', trend_shift, True, False)

    def nvi_trend(row):
        return trending(row, 'nvi', trend_shift, True, False)

    def smi_trend(row):
        return trending(row, 'smi', trend_shift, True, False)

    def macd_trend(row):
        return trending(row, 'macd', trend_shift, True, False)

    def roc_trend(row):
        return trending(row, 'roc', trend_shift, True, False)

    def histogram_trend(row):
        return trending(row, 'histogram', trend_shift, True, False)

    def percent_b_trend(row):
        return trending(row, 'percent_b', trend_shift, True, False)

    df['close_trend'] = df.apply(close_trend, axis=1)
    df['pvi_trend'] = df.apply(pvi_trend, axis=1)
    df['nvi_trend'] = df.apply(nvi_trend, axis=1)
    df['smi_trend'] = df.apply(smi_trend, axis=1)
    df['macd_trend'] = df.apply(macd_trend, axis=1)
    df['roc_trend'] = df.apply(roc_trend, axis=1)
    df['histogram_trend'] = df.apply(histogram_trend, axis=1)
    df['percent_b_trend'] = df.apply(percent_b_trend, axis=1)

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
    trend_shift = 6

    for i in range(trend_shift):
        j = i + 1
        df[f'next_close_{i}'] = df['close'].shift(-j)

    def next_close_trend(row):
        return trending(row, 'next_close', trend_shift, False, False, False)

    df[f'next_close'] = df.apply(next_close_trend, axis=1)
    
    def label(row):
        # growth indicators
        growth = row['next_close'] > 0.03
        p_trend = row['close_trend'] >= -0.3 and row['close_trend'] <= 0.3
        perb = row['percent_b'] < 0.5 and row['percent_b_trend'] > 0
        pvi = row['pvi_trend'] > 0
        roc = row['roc_trend'] > 0
        macd = row['histogram_trend'] > 0
        smi = row['smi_trend'] > 0

        if growth and pvi and perb and roc and macd and smi and p_trend:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < -0.03
        perb = row['percent_b'] > 0.5 and row['percent_b_trend'] < 0
        nvi = row['nvi_trend'] > 0
        roc = row['roc_trend'] < 0
        macd = row['histogram_trend'] < 0
        smi = row['smi_trend'] < 0

        if shrink and nvi and perb and nvi and roc and macd and smi and p_trend:
            return 'sell' 
        
        return 'hold'

    df['label'] = df.apply(label, axis=1)

    buys = len(df[df['label'] == 'buy'])
    sells = len(df[df['label'] == 'sell'])
    holds = len(df[df['label'] == 'hold'])

    print(f'buy count: {buys} sell count: {sells} hold count: {holds}')

    for i in range(trend_shift):
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