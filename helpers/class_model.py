from sklearn.model_selection import train_test_split
from helpers import features
from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import RandomForestClassifier

import pandas as pd

def create_model(symbol, window_data, evaluate=False):
    df = window_data.copy().dropna()

    if df.empty or df.shape[0] < 100:
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

        acc = metrics.accuracy_score(y_test, y_pred)
        prec = metrics.precision_score(y_test, y_pred, average='weighted')
        rec = metrics.recall_score(y_test, y_pred, average='weighted')
        f1 = metrics.f1_score(y_test, y_pred,average='weighted')
        kappa = metrics.cohen_kappa_score(y_test, y_pred)

        cm = metrics.confusion_matrix(y_test, y_pred)
        print(f'{symbol}')
        print('Accuracy:', acc)
        print('Precision:', prec)
        print('Recall:', rec)
        print('F1 Score:', f1)
        print('Cohens Kappa Score:', kappa)
        print('Confusion Matrix:\n', cm)

    return model
