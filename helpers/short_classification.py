from helpers import features

def classification(df):
    trend_shift = 6

    for i in range(trend_shift):
        j = i + 1
        df[f'next_close_{i}'] = df['close'].shift(-j)

    def next_close_trend(row):
        return features.trending(row, 'next_close', trend_shift, False, False, False)

    df[f'next_close'] = df.apply(next_close_trend, axis=1)
    
    def label(row):
        p_trend = row['close_trend'] >= -0.05 and row['close_trend'] <= 0.05

        # growth indicators
        growth = row['next_close'] > 0.03
        perb = row['percent_b_trend'] > 0
        pvi = row['pvi_trend'] > 0
        roc = row['roc_trend'] > 0 and row['roc'] < 0
        macd = row['histogram_trend'] > 0 and row['histogram'] < 0
        smi = row['smi_trend'] > 0

        if growth and pvi and perb and roc and macd and smi and p_trend:
            return 'buy' 

        # shrink indicators
        shrink = row['next_close'] < -0.03
        perb = row['percent_b_trend'] < 0
        nvi = row['nvi_trend'] > 0
        roc = row['roc_trend'] < 0 and row['roc'] > 0
        macd = row['histogram_trend'] < 0 and row['histogram'] > 0
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