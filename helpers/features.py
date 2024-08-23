from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote, CandlePart
from sklearn.preprocessing import MinMaxScaler

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
    #df.pop('open')
    #df.pop('high')
    #df.pop('low')
    #df.pop('close')
    #df.pop('vwap')

    trend_shift = 4

    for i in range(trend_shift):
        j = i + 1
        df.pop(f'close_{i}')
        df.pop(f'pvi_{i}')
        df.pop(f'nvi_{i}')
        df.pop(f'smi_{i}')

    #df.pop('close_trend')
    #df.pop('pvi_trend')
    #df.pop('nvi_trend')
    #df.pop('smi_trend')

    return df

def trends(df):
    trend_shift = 4

    for i in range(trend_shift):
        j = i + 1
        df[f'close_{i}'] = df['close'].shift(j)
        df[f'pvi_{i}'] = df['pvi'].shift(j)
        df[f'nvi_{i}'] = df['nvi'].shift(j)
        df[f'smi_{i}'] = df['smi'].shift(j)

    def close_trend(row):
        return trending(row, 'close', trend_shift, True, False)

    def pvi_trend(row):
        return trending(row, 'pvi', trend_shift, True, False)

    def nvi_trend(row):
        return trending(row, 'nvi', trend_shift, True, False)

    def smi_trend(row):
        return trending(row, 'smi', trend_shift, True, False)

    df['close_trend'] = df.apply(close_trend, axis=1)
    df['pvi_trend'] = df.apply(pvi_trend, axis=1)
    df['nvi_trend'] = df.apply(nvi_trend, axis=1)
    df['smi_trend'] = df.apply(smi_trend, axis=1)

    #scaler = MinMaxScaler(feature_range=(-1, 1))
    #df[['pvi_trend', 'nvi_trend', 'close_trend', 'smi_trend']] = scaler.fit_transform(df[['pvi_trend', 'nvi_trend', 'close_trend', 'smi_trend']])

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
        p_trend = row['close_trend'] > 0
        z_score = row['z_score'] > 1
        perb = row['percent_b'] >= 0.8
        pvi = row['pvi'] >= row['nvi'] and row['pvi_trend'] > 0 and row['nvi_trend'] < 0
        roc = row['roc'] > 0
        macd = row['histogram'] > 0 
        smi = row['smi_trend'] > 10

        if growth and pvi and z_score and perb and roc and macd and smi and p_trend:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < row['close']
        p_trend = row['close_trend'] < 0
        z_score = row['z_score'] < -1
        perb = row['percent_b'] <= 0.2
        nvi = row['nvi_trend'] < 0
        roc = row['roc'] < 0
        macd = row['macd'] < -1
        smi = row['smi_trend'] < 0

        if shrink and nvi and z_score and perb and nvi and roc and macd and smi and p_trend:
            return 'sell' 
        
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