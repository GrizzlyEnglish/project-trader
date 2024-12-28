from stock_indicators import indicators, Quote
from scipy.signal import argrelextrema

import numpy as np
import pandas as pd

small_window = 50
large_window = 200
length_KC = 20
mult_KC = 1.5
short_trend = 30
long_trend = 60

def get_hour(row):
    idx = row.name[1]
    return idx.hour

def get_minutes(row):
    idx = row.name[1]
    return idx.minute

def in_time(row):
    return row['hour'] >= 12 and row['hour'] < 19

def get_day_of_week(row):
    idx = row.name[1]
    return idx.dayofweek

def get_day_of_year(row):
    idx = row.name[1]
    return idx.dayofyear

def get_month(row):
    idx = row.name[1]
    return idx.month

def get_date(row):
    idx = row.name[1]
    return idx.year * (idx.month + idx.day)

def trending_arr(df, label, amt, name, prepend=False, postpend=False, reverse=True):
    arr = []

    if prepend:
        arr.append(df[label])

    for i in range(amt):
        arr.append(df[f'{label}_{i}_{name}'])

    if postpend:
        arr.append(df[label])

    if reverse:
        arr.reverse()

    return arr

def trending(df, label, amt, name, prepend=False, postpend=False, reverse=True):
    return slope(trending_arr(df, label, amt, name, prepend, postpend, reverse))

def slope(arr):
    if len(arr) <= 1:
        return 0
    arr = np.vstack(arr)
    poly_coeffs = np.polyfit(np.arange(len(arr)), np.vstack(arr), 1)
    poly_coeffs[np.isnan(poly_coeffs)] = 0  # possible speed-up: insert zeros where needed
    return poly_coeffs[0, :]  # slope only

def get_quotes(df):
    bars_i = df.reset_index()
    return [ 
        Quote(date, open, high, low, close, volume) 
            for date, open, high, low, close, volume 
            in zip(bars_i['timestamp'],
                bars_i['open'], 
                bars_i['high'], 
                bars_i['low'],
                bars_i['close'], 
                bars_i['volume'], strict=True)]

def feature_engineer_options(df):
    quotes = get_quotes(df)
    df = vortex_indicator(df, quotes)

    trend_col = ['pvi', 'nvi', 'close'] 
    df = trends(df, 4, 'short', trend_col)
    df = trends(df, 32, 'long', trend_col)

    df = last_two_bars(df, ['pvi', 'nvi', 'pvi_short_trend', 'nvi_short_trend', 'close_short_trend'])

    return df

def feature_engineer_bars(df):
    quotes = get_quotes(df)

    df.loc[:, 'change'] = df['close'].diff()

    # candle sticks
    df['candle_bar'] = df['close'] - df['open']
    df['candle_lines'] = df['high'] - df['low']

    #df['hour'] = df.apply(get_hour, axis=1)
    #df['minutes'] = df.apply(get_minutes, axis=1)
    #df['in_time'] = df.apply(in_time, axis=1)
    #df['date'] = df.apply(get_date, axis=1)
    #df['dayofweek'] = df.apply(get_day_of_week, axis=1)
    #df['dayofyear'] = df.apply(get_day_of_year, axis=1)
    #df['month'] = df.apply(get_month, axis=1)

    df = moving_average(df, quotes)
    df = macd(df, quotes)
    df = rate_of_change(df, quotes)
    #df = obv(df, quotes)
    df = rsi(df, quotes)
    df = vortex_indicator(df, quotes)
    df = vortex_indicator(df, quotes, 28, 'pvi_long', 'nvi_long')
    df = bands(df, quotes)
    df = smi(df, quotes)
    df = mfi(df, quotes)
    #df = truerange(df)
    #df = squeeze(df)

    trend_col = ['close', 'open', 'pvi', 'nvi', 'mfi', 'smi', 'pvi_long', 'nvi_long'] 
    df = trends(df, short_trend, 'short', trend_col)
    df = trends(df, long_trend, 'long', trend_col)

    #df = crossed(df, 'pvi', 1)
    #df = crossed(df, 'nvi', 1)
    #df = crossed(df, 'roc', 0)
    #df = crossed(df, 'macd', 0)
    #df = crossed(df, 'histogram', 0)

    #df = dip(df, short_trend, 'short')
    #df = dip(df, long_trend, 'long')

    df = last_two_bars(df, ['macd', 'pvi', 'roc', 'nvi', 'histogram', 'percent_b', 'pvi_long', 'nvi_long'])

    for col in df.select_dtypes(include=['bool']).columns:
        df[col] = df[col].astype(int)

    return df

def last_two_bars(df, columns):
    d = df.copy()[columns]
    shifted_df = d.shift(1)
    shifted_df = shifted_df.add_suffix(f'__last')
    df = pd.concat([df, shifted_df], axis=1, ignore_index=False)
    shifted_df = d.shift(2)
    shifted_df = shifted_df.add_suffix(f'__last__last')
    df = pd.concat([df, shifted_df], axis=1, ignore_index=False)
    del shifted_df
    return df

def long_indicator(row):
    out_bands = row['percent_b'] > 1 or row['percent_b'] < 0
    #if row['pvi__last'] < .7 and row['pvi'] > row['pvi__last'] and row['rsi'] <= 30:
        #return 1
    if out_bands and row['pvi'] < .7 and row['pvi_short_trend'] > 0:
        return -1
    if out_bands and row['nvi'] < .7 and row['nvi_short_trend'] > 0:
        return 1
    #if row['nvi__last'] < .7 and row['nvi'] > row['nvi__last'] and row['rsi'] >= 60:
        #return -1
    return 0

def vortext_indicator_long(row):
    if row['pvi_long'] > 1 and (row['pvi_long__last'] < 1 or row['pvi_long__last__last'] < 1):
        return 1
    
    if row['nvi_long'] > row['nvi_long__last'] and row['nvi_long__last'] > row['nvi_long__last__last'] and abs(row['nvi_long'] - row['nvi_long__last__last']) > .01 and row['nvi_long_short_trend'] > 0:
        return - 1
    
    return 0

def short_indicator(row):
    pvi = row['pvi'] < 1 and abs(row['pvi'] - row['pvi__last']) > 0.1 and abs(row['pvi__last'] - row['pvi__last__last']) > 0
    roc = row['roc'] > -0.05 and row['roc'] < 0.05 and row['roc'] > row['roc__last'] > row['roc__last__last'] and abs(row['roc'] - row['roc__last__last']) > 0.05
    pb = row['percent_b'] > row['percent_b__last'] and row['percent_b'] > .3
    candle = row.name[0] == 'QQQ' or row['candle_bar'] > 0.3
    mi_diff = row['mfi'] - row['smi']
    mi = (mi_diff > 0 and mi_diff < 80) or (row['smi'] > 0 and row['mfi'] < 32)

    if pvi and roc and candle and pb and mi:
        return 1

    nvi = row['nvi'] < 1 and abs(row['nvi'] - row['nvi__last']) > 0.1 and abs(row['nvi__last'] - row['nvi__last__last']) > 0
    roc = row['roc'] < 0.1 and row['roc'] > -0.15 and row['roc'] < row['roc__last'] < row['roc__last__last'] and abs(row['roc'] - row['roc__last__last']) > 0.05
    pb = row['percent_b'] < row['percent_b__last'] and row['percent_b'] < .8
    candle = row.name[0] == 'QQQ' or row['candle_bar'] < 0

    if nvi and roc and candle and pb:
        return -1

    return 0 

def dip(df, n, name):
    df[f'min_{name}'] = df.iloc[argrelextrema(df.close.values, np.less_equal,
                    order=n)[0]]['close']
    df[f'max_{name}'] = df.iloc[argrelextrema(df.close.values, np.greater_equal,
                    order=n)[0]]['close']
    
    df[f'min_{name}'] = df[f'min_{name}'].notna()
    df[f'max_{name}'] = df[f'max_{name}'].notna()
    return df

def crossed(df, col, crossed_value):
    df[f'{col}_cross_over'] = (df[col] >= crossed_value) & (df[col].shift() < crossed_value)
    df[f'{col}_cross_below'] = (df[col] <= crossed_value) & (df[col].shift() > crossed_value)
    return df

def trends(df, look_back, name, col_names):
    for i in range(look_back):
        j = i + 1
        df2 = df[col_names]
        df2 = df2.add_suffix(f'_{i}_{name}')
        df2 = df2.shift(j)
        df = pd.concat([df, df2], axis=1)

    for col_name in col_names:
        df[f'{col_name}_{name}_trend'] = trending(df, col_name, look_back, name, True, False)

    for col_name in col_names:
        for i in range(look_back):
            df.pop(f'{col_name}_{i}_{name}')

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

def vortex_indicator(df, quotes, lookback = 14, pvi = 'pvi', nvi = 'nvi'):
    results = indicators.get_vortex(quotes, lookback)

    df.loc[:, pvi] = [r.pvi for r in results]
    df.loc[:, nvi] = [r.nvi for r in results]

    return df

def moving_average(df, quotes):
    results = indicators.get_kama(quotes, 30, small_window, large_window)

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

def get_percentage_diff(initial_value, final_value): 
    profit_loss = final_value - initial_value 
    percent = (profit_loss / initial_value) * 100 
    return percent

def max_or_min_first(arr, delta, num): 
    filtered_arr = [value for value in arr if value > (num + delta) or value < (num - delta)] 
    if not filtered_arr:
        return 0
    return filtered_arr[0]