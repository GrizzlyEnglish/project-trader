from datetime import datetime

import math
import pandas as pd
import numpy as np

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

    if any(x == None or math.isnan(x) for x in arr):
        return 0

    return slope(arr)

def slope(arr):
    if len(arr) <= 1:
        return 0
    coeffs = np.polyfit(range(len(arr)), arr, 1)
    slope = coeffs[-2]
    return float(slope)

def trends(df):
    start = datetime.now()

    look_back = 5

    df['close_trend'] = df['close'].rolling(look_back+1).apply(slope)
    df['pvi_trend'] = df['pvi'].rolling(look_back+1).apply(slope)
    df['nvi_trend'] = df['nvi'].rolling(look_back+1).apply(slope)
    df['smi_trend'] = df['smi'].rolling(look_back+1).apply(slope)
    df['macd_trend'] = df['macd'].rolling(look_back+1).apply(slope)
    df['roc_trend'] = df['roc'].rolling(look_back+1).apply(slope)
    df['histogram_trend'] = df['histogram'].rolling(look_back+1).apply(slope)
    df['percent_b_trend'] = df['percent_b'].rolling(look_back+1).apply(slope)
    df['height_trend'] = df['height'].rolling(look_back+1).apply(slope)

    print(f'Trends function took {datetime.now() - start}')

    return df

data = []

for i in range(10000):
    data.append([545.9,	0.3333398862,	0.01673619117,	0.2111060119,	55.95725508,	1.100447539,	0.8652411735,	0.8219623901,	1.808441041,	46.79554862])

columns = ['close', 'macd',	'histogram', 'roc', 'rsi', 'pvi', 'nvi', 'percent_b', 'height', 'smi']

df = pd.DataFrame(columns=columns, data=data)

df = trends(df)

print(df)