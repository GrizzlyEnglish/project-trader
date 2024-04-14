from sklearn.preprocessing import StandardScaler
from helpers.features import feature_engineer_df
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

def get_model(stock):
    stock_path = stock.replace('/', '.')
    path = "generated/%s.model.keras" % stock_path
    file_exists = exists(path)
    file_to_old = False

    if file_exists:
        file_to_old = is_file_older_than_x_days(path)

    if file_exists and not file_to_old :
        return keras.models.load_model(path, compile=True)
    
    return None

def generate_model(stock, window_data):
    stock_path = stock.replace('/', '.')
    path = "generated/%s.model.keras" % stock_path
    return create_model(stock, path, window_data)

def create_model(stock, path, window_data):
    df = window_data

    if df.empty:
        print("No data available for %s" % stock)

    df = feature_engineer_df(df)

    print(df)

    X = df.iloc[:, 0:-1]
    Y = df.iloc[:, -1]

    print(X)

    split_data = int(len(df)*0.7)

    X_train, X_test, Y_train, Y_test = X.iloc[:split_data, :], X.iloc[split_data:, :], Y.iloc[:split_data], Y.iloc[split_data:]

    print(X_train)

    scaler = StandardScaler()

    X_train = scaler.fit_transform(X_train)

    X_test = scaler.transform(X_test)

    model = tf.keras.Sequential([
        keras.layers.LSTM(60, return_sequences=True),
        keras.layers.Dropout(0.3),
        keras.layers.LSTM(120, return_sequences=False),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(20),
        keras.layers.Dense(1),
    ])

    model.compile(optimizer = 'adam', loss = 'mean_squared_error', metrics = ['accuracy'])

    X_train = np.expand_dims(X_train, 1)
    model.fit(X_train, Y_train, batch_size = 750, epochs = 100)

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