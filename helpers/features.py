#import numba
import numpy as np

def feature_engineer_df(df):
    small_window = 50
    large_window = 200

    df.loc[:, 'ma_short'] = df['close'].rolling(window=small_window).mean()
    df.loc[:, 'ma_long'] = df['close'].rolling(window=large_window).mean()
    df.loc[:, 'close_var'] = get_percentage_diff(df['open'], df['close'])
    df.loc[:, 'gap'] = df['close'] - df['open']
    df.loc[:, 'next_open'] = df['open'].shift(-1)
    df.loc[:, 'change'] = df['close'].diff()

    df.loc[:, 'ema_short'] = df['close'].ewm(span=12).mean()
    df.loc[:, 'ema_long'] = df['close'].ewm(span=26).mean()

    df.loc[:, 'macd'] = df['ema_short'] - df['ema_long']
    df.loc[:, 'signal'] = df['macd'].ewm(span=9).mean()

    df = obv(df)

    df = rsi(df)

    df.loc[:, 'ma_short_f_2'] = df['ma_short'].shift(-small_window)
    df.loc[:, 'ma_long_f_2'] = df['ma_long'].shift(-large_window)

    # Drop stuff to not overfit
    df.drop('ema_short', axis=1, inplace=True)
    df.drop('ema_long', axis=1, inplace=True)

    df = df.dropna()

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