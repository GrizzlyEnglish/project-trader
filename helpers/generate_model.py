from sklearn.preprocessing import StandardScaler
from os.path import exists
from tensorflow import keras

import os
import numpy as np
import tensorflow as tf
import time

def is_file_older_than_x_days(filepath, days=7):
    file_mtime = os.path.getmtime(filepath)
    current_time = time.time()
    age_in_seconds = current_time - file_mtime
    age_in_days = age_in_seconds / (24 * 3600)  

    return age_in_days > days

def get_path(symbol):
    stock_path = symbol.replace('/', '.')
    return "generated/%s.model.keras" % stock_path

def get_model(symbol, window_data, force=False):
    path = get_path(symbol)
    file_exists = exists(path)
    file_to_old = False

    if file_exists:
        file_to_old = is_file_older_than_x_days(path)

    if not force and file_exists and not file_to_old :
        return keras.models.load_model(path, compile=True)
    
    return create_model(symbol, path, window_data)

def create_model(symbol, path, window_data):
    df = window_data

    if df.empty:
        print("No data available for %s" % symbol)

    print(df)

    X = df.iloc[:, 0:-2]
    Y = df.iloc[:, -2:]

    print(X)
    print(Y)

    split_data = int(len(df)*0.7)

    X_train, X_test, Y_train, Y_test = X.iloc[:split_data, :], X.iloc[split_data:, :], Y.iloc[:split_data], Y.iloc[split_data:]

    print(X_train)

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)

    X_test = scaler.transform(X_test)

    model = tf.keras.Sequential([
        keras.layers.LSTM(130, return_sequences=True),
        keras.layers.Dropout(0.37),
        keras.layers.LSTM(65, return_sequences=False),
        keras.layers.Dense(2),
    ])

    model.compile(optimizer = 'adam', loss = 'mean_squared_error', metrics = ['accuracy'])

    X_train = np.expand_dims(X_train, 1)
    model.fit(X_train, Y_train, batch_size = 120, epochs = 100)

    model.save(path)

    '''
    X_test = np.expand_dims(X_test, 1)
    Y_pred = model.predict(X_test)

    for i in range(len(Y_test)):
        predicted = Y_pred[i][0]
        test = Y_test.iloc[i]
        print("%s   %s", (test, predicted))
    '''

    return model