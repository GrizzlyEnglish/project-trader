import numpy as np
from sklearn.preprocessing import StandardScaler

def determine_status(df, model):
    status = 'hold'

    df['ewm_12'] = df['close'].ewm(span=12, adjust=False).mean()
    df['ewm_24'] = df['close'].ewm(span=24, adjust=False).mean()
    print(df)

    left_trend = determine_trend(df['ewm_12'].iloc[0], df['ewm_12'].iloc[-1])

    if len(df) > 0:
        scaler = StandardScaler()
        split_data = int(len(df)*0.7)
        scaler.fit_transform(df.iloc[:split_data, :])
        df_test = scaler.transform(df.iloc[split_data:, :])
        df_test = np.expand_dims(df_test, 1)
        predicted = model.predict(df_test)
        right_trend = determine_trend(df['ewm_12'].iloc[-1], predicted[-1][0])
    else:
        right_trend = 'down'

    print("     Left trend is %s and right trend is %s" % (left_trend, right_trend))

    if right_trend == 'up':
        status = 'buy'
    elif left_trend == 'up' and right_trend == 'down':
        status = 'sell'

    print("     Setting status to %s " % status)
    return status


def determine_trend(start, end):
    trend = 'empty'

    if start < end:
        trend = 'up'
    else:
        trend = 'down'

    return trend