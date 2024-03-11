import math

def determine_status(df, column, span, trade_factor):
    status = 'hold'

    df['ewm'] = df[column].ewm(span=span, adjust=False).mean()
    print(df)

    split = math.floor(span / 2)

    left = df['ewm'][1:split]
    right = df['ewm'][split:span]

    left_trend = determine_trend(left, trade_factor)
    right_trend = determine_trend(right, trade_factor)

    print("     Left trend is %s and right trend is %s" % (left_trend, right_trend))

    if left_trend == 'down' and right_trend == 'up':
        status = 'buy'
    elif left_trend == 'up' and right_trend == 'down':
        status = 'sell'

    print("     Setting status to %s " % status)
    return status


def determine_trend(df, trade_factor):
    # Assume down
    trend = 'empty'

    if df.empty:
        return trend

    window_factor = df.iloc[0] / df.iloc[-1]
    window_mean = df.mean()

    if window_factor > trade_factor:
        trend = 'up'
    else:
        trend = 'down'

    return trend