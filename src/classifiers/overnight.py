import pandas as pd

def classification(bars, look_forward):
    def day_label(row):
        open_diff = row['daydiff_open']
        if open_diff < down_diff:# and row['close_trend'] < 0 and row['nvi_trend'] > 0:
            return 'sell'
        elif open_diff > up_diff:# and row['close_trend'] > 0 and row['pvi_trend'] > 0:
            return 'buy'
        else:
            return 'hold'

    bars = bars.loc[(bars['hour'] == 13) | (bars['hour'] == 19)].copy()

    bars['next_open'] = bars['open'].shift(-1)

    def daydiff_open(row):
        return row['next_open']-row['close']

    bars['daydiff_open'] = bars.apply(daydiff_open, axis=1)

    bars = bars[bars['hour'] == 19]

    up_b = bars[bars['daydiff_open'] > 0]['daydiff_open']
    down_b = bars[bars['daydiff_open'] < 0]['daydiff_open']
    up_diff = up_b.mean() #+ up_b.std()
    down_diff = down_b.mean() #- down_b.std()

    print(f'up diff {up_diff} down diff {down_diff}')
        
    bars['label'] = bars.apply(day_label, axis=1)

    buys = len(bars[bars['label'] == 'buy'])
    sells = len(bars[bars['label'] == 'sell'])
    holds = len(bars[bars['label'] == 'hold'])

    print(f'overnight buy count: {buys} sell count: {sells} hold count: {holds}')

    bars.pop('next_open')
    bars.pop('daydiff_open')

    return bars, up_diff, down_diff