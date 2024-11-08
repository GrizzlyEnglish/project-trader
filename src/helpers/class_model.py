from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn import metrics, preprocessing
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC

import os
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

def generate_model(symbol, bars, classification):
    bars = classification(bars)

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
    predicitons = []
    for key in model.keys():
        pred = model[key].predict(bars)
        pred = [int_to_label(p) for p in pred]
        predicitons.append(pred[-1])

    return predicitons

def group_bars(bars):
    group = int(os.getenv('BAR_GROUP'))
    new_bars = bars.copy()
    for i in range(group):
        j = i + 1
        shifted_df = bars.shift(j)
        shifted_df = shifted_df.add_suffix(f'___{i}')
        if f'label___{i}' in shifted_df.columns:
            shifted_df.pop(f'label___{i}')
        new_bars = pd.concat([new_bars, shifted_df], axis=1, ignore_index=False)
        del shifted_df
    del bars
    return new_bars.dropna()

def preprocess_bars(bars):
    min_max_scaler = preprocessing.MinMaxScaler()
    return min_max_scaler.fit_transform(bars)

def create_model(symbol, df):
    df = df.dropna()

    if df.empty:
        print("%s has no data or not enough data to generate a model" % symbol)
        return None, 0

    df = group_bars(df)
    
    target = df['label']
    feature = df.drop('label', axis=1)

    feature = preprocess_bars(feature)

    model = None
    acc = 0
    matrix = None

    for i in range(10):
        x_train, x_test, y_train, y_test = train_test_split(feature, 
                                                            target, 
                                                            shuffle = True, 
                                                            test_size=0.65, 
                                                            random_state=1)
        m = RandomForestClassifier(max_depth=2400, random_state=43)
        m.fit(x_train, y_train)

        y_pred = m.predict(x_test)
        cm = metrics.confusion_matrix(y_test, y_pred)
        rys = (cm[0][0] + cm[1][1])/(cm[0][0] + cm[1][1] + cm[2][0] + cm[2][1] + cm[1][0] + cm[0][1])

        if rys > acc:
            model = m
            acc = rys
            matrix = cm

    print(f'{symbol}')
    print(f'Ryans Kappa Score: {acc}')
    print('Confusion Matrix:\n', matrix)

    return model, rys
