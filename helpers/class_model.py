from sklearn.preprocessing import StandardScaler
from sklearn import tree
from sklearn.model_selection import train_test_split
from helpers import features
from sklearn import metrics
from sklearn.svm import SVC
from skmultilearn.problem_transform import BinaryRelevance
from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils import shuffle

import os
import numpy as np
import tensorflow as tf
import time
import joblib

def create_model(symbol, window_data, type, evaluate=False):
    df = window_data.copy().dropna()

    if df.empty or df.shape[0] < 100:
        print("%s has no data or not enough data to generate a model" % symbol)
        return None
    
    if type == 'short':
        df = features.short_classification(df)
    elif type == 'long':
        df = features.long_classification(df)
    else:
        print("Wrong type passed")
        return None

    df = df.dropna()

    print(df)

    df['label'] = df['label'].apply(features.label_to_int)

    target = df['label']
    feature = df.drop('label', axis=1)

    x_train, x_test, y_train, y_test = train_test_split(feature, 
                                                        target, 
                                                        shuffle = True, 
                                                        test_size=0.2, 
                                                        random_state=1)

    model = tree.DecisionTreeClassifier(random_state=0)
    model.fit(x_train, y_train)

    if evaluate:
        y_pred = model.predict(x_test)

        acc = metrics.accuracy_score(y_test, y_pred)
        prec = metrics.precision_score(y_test, y_pred, average='weighted')
        rec = metrics.recall_score(y_test, y_pred, average='weighted')
        f1 = metrics.f1_score(y_test, y_pred,average='weighted')
        kappa = metrics.cohen_kappa_score(y_test, y_pred)

        y_pred_proba = model.predict_proba(x_test)[::,1]

        cm = metrics.confusion_matrix(y_test, y_pred)
        print('Accuracy:', acc)
        print('Precision:', prec)
        print('Recall:', rec)
        print('F1 Score:', f1)
        print('Cohens Kappa Score:', kappa)
        print('Confusion Matrix:\n', cm)

    return model
