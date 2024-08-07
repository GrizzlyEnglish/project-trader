from sklearn.cluster import KMeans
from stock_indicators import indicators, Quote

import numpy as np
import math

small_window = 50
large_window = 200

def fully_feature_engineer(df):
    feature_engineer_df(df)
    feature_engineer_future_df(df)
    return df

def feature_engineer_df(df):
    df.loc[:, 'ma_short'] = df['close'].rolling(window=small_window).mean()
    df.loc[:, 'ma_long'] = df['close'].rolling(window=large_window).mean()
    df.loc[:, 'gap'] = df['close'] - df['open']
    df.loc[:, 'next_open'] = df['open'].shift(-1)
    df.loc[:, 'change'] = df['close'].diff()

    df.loc[:, 'ema_short'] = df['close'].ewm(span=12).mean()
    df.loc[:, 'ema_long'] = df['close'].ewm(span=26).mean()

    df.loc[:, 'macd'] = df['ema_short'] - df['ema_long']
    df.loc[:, 'signal'] = df['macd'].ewm(span=9).mean()

    df = rate_of_change(df)

    df = close_variance(df)

    df = obv(df)

    df = rsi(df)

    df = support_resistance(df)

    return df

def rate_of_change(df):
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
    
    results = indicators.get_roc(quotes, 14)

    df.loc[:, 'roc'] = [r.roc for r in results]
    df.loc[:, 'roc_sma'] = [r.roc_sma for r in results]
    df.loc[:, 'roc_momentum'] = [r.momentum for r in results]

    return df

def close_variance(df):
    df.loc[:, 'difference'] = df['open'] - df['close']
    df.loc[:, 'close_var'] = (df['difference'] / ((df['open'] + df['close']) / 2)) * 100
    df.pop('difference')
    return df

def feature_engineer_future_df(df):
    df.loc[:, 'ma_short_f_2'] = df['ma_short'].shift(-small_window)
    df.loc[:, 'ma_long_f_2'] = df['ma_long'].shift(-large_window)

    # TODO: Make this be the end of the market day for the next day?
    df.loc[:, 'future_close'] = df['close'].shift(-60*24)

    return df

def obv(df):
    df.loc[:, 'obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
    return df

def get_percentage_diff(previous, current):
    try:
        absolute_diff = current - previous
        average_value = (current + previous) / 2
        percentage = (absolute_diff / average_value) * 100.0
        rounded_percentage = round(percentage)
        
        return rounded_percentage
    except ZeroDivisionError:
        return float('inf')  # Infinity
    
def rsi(df):
    df.loc[:, 'gain'] = df.change.mask(df.change < 0, 0.0)
    df.loc[:, 'loss'] = -df.change.mask(df.change > 0, -0.0)
    df.loc[:, 'avg_gain'] = rma(df.gain.to_numpy(), 14)
    df.loc[:, 'avg_loss'] = rma(df.loss.to_numpy(), 14)
    df.loc[:, 'rs'] = df.avg_gain / df.avg_loss
    df.loc[:, 'rsi'] = 100 - (100 / (1 + df.rs))

    df.pop('gain')
    df.pop('loss',)
    df.pop('avg_gain')
    df.pop('avg_loss')
    df.pop('rs')
    
    return df

#@numba.jit
def rma(x, n):
    """Running moving average"""
    a = np.full_like(x, np.nan)
    a[n] = x[1:n+1].mean()
    for i in range(n+1, len(x)):
        a[i] = (a[i-1] * (n - 1) + x[i]) / n
    return a

def support_resistance(df):
    cluster_count = math.floor(len(df.index) * .4)
    close = np.array(df['close']).reshape(-1, 1)
    kmeans = KMeans(n_clusters=cluster_count).fit(close)
    clusters = kmeans.predict(close)
    min_max_values = []

    for i in range(cluster_count):
        min_max_values.append([np.inf, -np.inf])

    for i in range(len(close)):
        cluster = clusters[i]
        i_close = close[i][0]
        if i_close < min_max_values[cluster][0]:
            min_max_values[cluster][0] = i_close
        if i_close > min_max_values[cluster][1]:
            min_max_values[cluster][1] = i_close

    resistance = []
    support = []
    for i in range(len(close)):
        cluster = clusters[i]
        pair = min_max_values[cluster]
        resistance.append(pair[0])
        support.append(pair[1])

    df['resistance'] = resistance
    df['support'] = support

    return df