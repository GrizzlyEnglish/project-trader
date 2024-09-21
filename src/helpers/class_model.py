from sklearn.model_selection import train_test_split
from src.helpers import features, get_data
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

import pandas as pd
import os

def generate_model(symbol, bars):
    buys = len(bars[bars.label == 'buy'])
    sells = len(bars[bars.label == 'sell'])
    holds = min((buys + sells) * 2, len(bars[bars['label'] == 'hold']))

    bars = pd.concat([
        bars[bars.label == 'buy'],
        bars[bars.label == 'sell'],
        bars[bars.label == 'hold'].sample(n=holds)
    ])

    print(f'Model bars buy count: {buys} sell count: {sells} hold count: {holds}')

    bars['label'] = bars['label'].apply(label_to_int)

    model, accuracy = create_model(symbol, bars)

    return model, bars, accuracy, buys, sells

def classify_symbols(symbol_info, classification, market_client, end, time_unit):
    pred_bar_amt = int(os.getenv('PRED_BARS'))
    classified = []
    for info in symbol_info:
        symbol = info['symbol']
        day_diff = info['day_diff']
        time_window = info['time_window']
        look_back = info['look_back']
        look_forward = info['look_forward']

        bars = get_model_bars(symbol, market_client, end - timedelta(days=day_diff), end + timedelta(days=1), time_window, classification, look_back, look_forward, time_unit)
        model_bars = bars.head(len(bars) - pred_bar_amt)
        pred_bars = bars.tail(pred_bar_amt)

        pred_bars.pop("label")

        model, model_bars, accuracy, buys, sells = generate_model(symbol, model_bars)

        class_type = predict(model, pred_bars)

        print(f'{symbol} classification={class_type} on bar {pred_bars.index[0][1]}')

        classified.append({
            'symbol': symbol,
            'class': class_type,
        })

    return classified

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
    bars = classification(bars, look_forward)
    bars = features.drop_prices(bars, look_back)
    return bars

def predict(model, bars):
    pred = model.predict(bars)
    pred = [int_to_label(p) for p in pred]
    pred = [s for s in pred if s != 'Hold']
    class_type = "Hold"
    if len(pred) > 0 and all(x == pred[0] for x in pred):
        class_type = "Buy"
        if pred[0] == 'Sell':
            class_type = "Sell"
    return class_type

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
