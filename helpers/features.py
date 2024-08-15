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
    df.pop('next_open')
    df.pop('support')
    df.pop('resistance')

    return df

def fully_feature_engineer(df):
    feature_engineer_df(df)
    feature_engineer_future_df(df)
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

    df.loc[:, 'gap'] = df['close'] - df['open']
    df.loc[:, 'next_open'] = df['open'].shift(-1)
    df.loc[:, 'change'] = df['close'].diff()

    df = moving_average(df, quotes)

    df = macd(df, quotes)

    df = rate_of_change(df, quotes)

    df = obv(df, quotes)

    df = rsi(df, quotes)

    df = vortex_indicator(df, quotes)

    df = support_resistance(df)

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
    #df.loc[:, 'roc_momentum'] = [r.momentum for r in results]

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

def long_classification(df):
    day_bars = (60 * 5)

    df['1d_close'] = df['close'].shift(-day_bars)
    df['5d_close'] = df['close'].shift(-(day_bars * 5))

    def label(row):
        if math.isnan(row['1d_close']) or math.isnan(row['5d_close']):
            return 'hold'

        long_s_diff = get_percentage_diff(row['close'], row['1d_close'],False)
        long_l_diff = get_percentage_diff(row['close'], row['5d_close'],False)

        if long_l_diff > 3 and long_s_diff > 1:
            return 'buy_long' 
        elif long_l_diff < -3 and long_s_diff < -1:
            return 'sell_long' 
        else:
            return 'hold'

    df['label'] = df.apply(label, axis=1)

    df.pop('1d_close')
    df.pop('5d_close')

    return df

def short_classification(df, time_window):
    one_hour = math.floor(60 / time_window)

    df['1h_close'] = df['close'].shift(3)
    df['2h_close'] = df['close'].shift(1)

    def label(row):
        if math.isnan(row['1h_close']) or math.isnan(row['2h_close']):
            return None
        
        one_diff = row['1h_close'] - row['close']
        three_diff = row['2h_close'] - row['close']

        growth = one_diff > 0 and three_diff > 0
        shrink = one_diff < 0 and three_diff < 0

        if growth:
            # and row['roc'] > 0 and (row['pvi'] > row['nvi']) and row['macd'] > 0:
            return 'buy_short' 
        elif shrink:
            # and row['roc'] < 0 and (row['pvi'] < row['nvi']) and row['macd'] > 0:
            return 'sell_short' 
        else:
            return 'hold'

    df['label'] = df.apply(label, axis=1)

    df.pop('1h_close')
    df.pop('2h_close')

    return df

def label_to_int(row):
    if row == 'buy_long': return 0
    elif row == 'sell_long': return 1
    elif row == 'buy_short': return 2
    elif row == 'sell_short': return 3
    elif row == 'hold': return 4

def int_to_label(row):
    if row == 0: return 'Buy long'
    elif row == 1: return 'Sell long'
    elif row == 2: return 'Buy short'
    elif row == 3: return 'Sell short'
    elif row == 4: return 'Hold'