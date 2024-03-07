def determine_trend(df, small_window, large_window):
    trend = 'up'

    small_r = df.rolling(small_window).mean()
    big_r = df.rolling(large_window).mean()

    print('Small window df')
    print(small_r)

    print('Large window df')
    print(big_r)

    # TODO: Do I need to do a rolling average of these also?
    if small_r.values[-1] <= big_r.values[-1]:
        trend = 'down'

    return trend