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

def generate_model(symbol, info, market_client, classification, end):
    day_diff = info['day_diff']
    time_window = int(info['time_window'])
    look_back = info['look_back']
    look_forward = info['look_forward']
    time_unit = info['time_unit']

    m_st = end - timedelta(days=day_diff- 1)
    m_end = end
    print(f'Model start {m_st} model end {m_end}')
    bars, call_var, put_var = get_model_bars(symbol, market_client, m_st, m_end, time_window, classification, look_back, look_forward, time_unit)

    bars, buys, sells = sample_bars(bars)

    bars['label'] = bars['label'].apply(label_to_int)

    model, accuracy = create_model(symbol, bars)

    return {
        'model': model,
        'bars': bars,
        'accuracy': accuracy,
        'buys': buys,
        'sells': sells,
        'call_variance': call_var,
        'put_variance': put_var
    }

def label_to_int(row):
    if row == 'buy': return 0
    elif row == 'sell': return 1
    elif row == 'hold': return 2

def int_to_label(row):
    if row == 0: return 'Buy'
    elif row == 1: return 'Sell'
    elif row == 2: return 'Hold'

def get_model_bars(symbol, market_client, start, end, time_window, classification, look_back, look_forward, time_unit):
    bars = get_data.get_bars(symbol, start, end, market_client, time_window, time_unit)
    bars = features.feature_engineer_df(bars, look_back)
    bars, call_var, put_var = classification(bars, look_forward)
    bars = features.drop_prices(bars, look_back)
    return bars, call_var, put_var

def get_prediction_bars(symbol, model_info, market_client):
    time_window = int(model_info['time_window'])
    look_back = model_info['look_back']
    time_unit = model_info['time_unit']
    day_diff = model_info['day_diff']

    end = datetime.now()
    start = end - timedelta(days=day_diff)

    bars = get_data.get_bars(symbol, start, end, market_client, time_window, time_unit)
    bars = features.feature_engineer_df(bars, look_back)
    bars = features.drop_prices(bars, look_back)

    return bars

def predict(model, bars):
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
