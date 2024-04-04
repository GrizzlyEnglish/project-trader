def feature_engineer_df(df, addFuture = True):
    df['ewm_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ewm_24'] = df['close'].ewm(span=24, adjust=False).mean()
    df['close_var'] = get_percentage_diff(df['open'], df['close'])
    df['gap'] = df['close'] - df['open']
    df['next_open'] = df['open'].shift(-1)
    if df['open'].iloc[0] < 0:
        df = df * 100
    if addFuture:
        future_ewm = []
        for i in range(len(df)):
            start_row = i
            end_row = min(i + 5, len(df))  
            subset = df.iloc[start_row:end_row]
            ewm_12_f = subset['ewm_12'].ewm(span=12, adjust=False).mean()
            future_ewm.append(ewm_12_f.iloc[-1])

        df.insert(9, 'ewm_12_f_2', future_ewm)
    return df

def get_percentage_diff(previous, current):
    try:
        percentage = (current - previous) / ((current + previous) / 2) * 100
    except ZeroDivisionError:
        percentage = float('inf')
    return percentage