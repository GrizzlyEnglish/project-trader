def classification(bars):
    def day_label(row):
        open_diff = row['daydiff_open']
        if open_diff < down_diff:
            return 'sell'
        elif open_diff > up_diff:
            return 'buy'
        else:
            return 'hold'

    def get_time(row):
        idx = row.name[1]
        return f'{idx.hour}:{idx.minute}'

    def get_day_of_week(row):
        idx = row.name[1]
        return idx.dayofweek

    def get_day_of_year(row):
        idx = row.name[1]
        return idx.dayofyear

    def get_month(row):
        idx = row.name[1]
        return idx.month

    bars['dayofweek'] = bars.apply(get_day_of_week, axis=1)
    bars['dayofyear'] = bars.apply(get_day_of_year, axis=1)
    bars['month'] = bars.apply(get_month, axis=1)
    bars['time'] = bars.apply(get_time, axis=1)
    bars = bars[bars['time'] != '13:0']

    bars['next_open'] = bars['open'].shift(-1)
    bars['next_close'] = bars['close'].shift(-1)
    bars['daydiff_open'] = bars['next_open'] - bars['close']

    for i in range(10):
        bars[f'prev_ah_{i}'] = bars['daydiff_open'].shift(i)

    bars = bars[bars['time'] == '20:0']
    bars.pop('time')

    up_diff = bars[bars['daydiff_open'] > 0]['daydiff_open'].mean()
    down_diff = bars[bars['daydiff_open'] < 0]['daydiff_open'].mean()

    print(f'up diff {up_diff} down diff {down_diff}')
        
    bars['label'] = bars.apply(day_label, axis=1)

    buys = len(bars[bars['label'] == 'buy'])
    sells = len(bars[bars['label'] == 'sell'])
    holds = len(bars[bars['label'] == 'hold'])

    print(f'overnight buy count: {buys} sell count: {sells} hold count: {holds}')

    return bars