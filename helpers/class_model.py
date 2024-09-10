from sklearn.model_selection import train_test_split
from helpers import features
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestClassifier

import pandas as pd

def create_model(symbol, window_data, evaluate=False):
    df = window_data.copy().dropna()

    if df.empty:
        print("%s has no data or not enough data to generate a model" % symbol)
        return None
    
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

    if evaluate:
        y_pred = model.predict(x_test)

        kappa = metrics.cohen_kappa_score(y_test, y_pred)

        cm = metrics.confusion_matrix(y_test, y_pred)
        print(f'{symbol}')
        print('Cohens Kappa Score:', kappa)
        print(f'Ryans Score: {(cm[0][0] + cm[1][1])/(cm[0][0] + cm[1][1] + cm[2][0] + cm[2][1] + cm[1][0] + cm[0][1])}')
        print('Confusion Matrix:\n', cm)

    return model
