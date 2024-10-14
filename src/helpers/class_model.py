from sklearn.model_selection import train_test_split
from src.helpers import features, get_data
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

import pandas as pd

def sample_bars(bars):
    buys = len(bars[bars.label == 'buy'])
    sells = len(bars[bars.label == 'sell'])
    holds = min((buys + sells) * 2, len(bars[bars['label'] == 'hold']))

    bars = pd.concat([
        bars[bars.label == 'buy'],
        bars[bars.label == 'sell'],
        bars[bars.label == 'hold'].sample(n=holds)
    ])

    print(f'Model bars buy count: {buys} sell count: {sells} hold count: {holds}')

    return bars, buys, sells

def generate_model(symbol, amount_days, market_client, classification, end, time_window=1, time_unit='Min'):
    m_st = end - timedelta(days=amount_days-1)
    m_end = end

    bars = get_data.get_model_bars(symbol, market_client, m_st, m_end, time_window, classification, time_unit)
    print(f'Model start {m_st} model end {m_end} with bar counr of {len(bars)}')

    bars, buys, sells = sample_bars(bars)

    bars['label'] = bars['label'].apply(label_to_int)

    model, accuracy = create_model(symbol, bars)

    return {
        'model': model,
        'bars': bars,
        'accuracy': accuracy,
        'buys': buys,
        'sells': sells,
    }

def label_to_int(row):
    if row == 'buy': return 0
    elif row == 'sell': return 1
    elif row == 'hold': return 2

def int_to_label(row):
    if row == 0: return 'Buy'
    elif row == 1: return 'Sell'
    elif row == 2: return 'Hold'

def classify(model, bars):
    pred = model.predict(bars)
    pred = [int_to_label(p) for p in pred]
    return pred

def create_model(symbol, window_data):
    df = window_data.copy().dropna()

    if df.empty:
        print("%s has no data or not enough data to generate a model" % symbol)
        return None, 0
    
    df = df.dropna()
 
    target = df['label']
    feature = df.drop('label', axis=1)

    x_train, x_test, y_train, y_test = train_test_split(feature, 
                                                        target, 
                                                        shuffle = True, 
                                                        test_size=0.65, 
                                                        random_state=1)

    model = RandomForestClassifier(max_depth=30, random_state=0)
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)

    kappa = metrics.cohen_kappa_score(y_test, y_pred)

    cm = metrics.confusion_matrix(y_test, y_pred)
    rys = (cm[0][0] + cm[1][1])/(cm[0][0] + cm[1][1] + cm[2][0] + cm[2][1] + cm[1][0] + cm[0][1])

    print(f'{symbol}')
    print('Cohens Kappa Score:', kappa)
    print(f'Ryans Kappa Score: {rys}')
    print('Confusion Matrix:\n', cm)

    return model, rys
