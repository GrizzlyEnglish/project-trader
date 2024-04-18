#import numba
import numpy as np

def feature_engineer_df(df, addFuture = True):
    df['ewm_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ewm_24'] = df['close'].ewm(span=24, adjust=False).mean()
    df['close_var'] = get_percentage_diff(df['open'], df['close'])
    df['gap'] = df['close'] - df['open']
    df['next_open'] = df['open'].shift(-1)
    df['change'] = df['close'].diff()

    df = rsi(df)

    df.fillna(0, inplace=True)

    if addFuture:
        future_ewm = []
        for i in range(len(df)):
            start_row = i
            end_row = min(i + 5, len(df))  
            subset = df.iloc[start_row:end_row]
            ewm_12_f = subset['ewm_12'].ewm(span=12, adjust=False).mean()
            future_ewm.append(ewm_12_f.iloc[-1])
        df.insert(14, 'ewm_12_f_2', future_ewm)
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
    df['gain'] = df.change.mask(df.change < 0, 0.0)
    df['loss'] = -df.change.mask(df.change > 0, -0.0)
    df['avg_gain'] = rma(df.gain.to_numpy(), 14)
    df['avg_loss'] = rma(df.loss.to_numpy(), 14)
    df['rs'] = df.avg_gain / df.avg_loss
    df['rsi'] = 100 - (100 / (1 + df.rs))

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