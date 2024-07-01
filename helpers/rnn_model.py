from sklearn.preprocessing import RobustScaler
from os.path import exists
from tensorflow import keras

import os
import numpy as np
import tensorflow as tf
import time
import joblib

def get_prediction(symbol, bars, force_model):
    bars = bars.dropna()

    prediction_data = bars.copy()[-20:]
    model_data= bars.copy()[:-20]

    # cant predict with nan
    model_data = model_data.dropna()

    if model_data.empty:
        return None, None, None

    rnn = get_model(symbol, model_data, force_model)

    if rnn == None:
        return None, None, None

    model = rnn['model']
    x_scaler = rnn['x_scaler']
    y_scaler = rnn['y_scaler']

    # Values to predict
    prediction_data.drop('ma_short_f_2', axis=1, inplace=True)
    prediction_data.drop('ma_long_f_2', axis=1, inplace=True)
    prediction_data.drop('future_close', axis=1, inplace=True)

    df_test = x_scaler.fit_transform(prediction_data)
    df_test = np.expand_dims(df_test, 1)

    predicted = model.predict(df_test)
    predicted = y_scaler.inverse_transform(predicted)

    shortPoints = [value[1][0] for value in enumerate(predicted)] 
    longPoints = [value[1][1] for value in enumerate(predicted)] 
    future_close = [value[1][2] for value in enumerate(predicted)] 

    return shortPoints, longPoints, future_close


def is_file_older_than_x_days(filepath, days=30):
    file_mtime = os.path.getmtime(filepath)
    current_time = time.time()
    age_in_seconds = current_time - file_mtime
    age_in_days = age_in_seconds / (24 * 3600)  

    return age_in_days > days

def get_model_path(symbol):
    stock_path = symbol.replace('/', '.')
    return "generated/%s.model.keras" % stock_path

def get_scaler_base_path(symbol):
    stock_path = symbol.replace('/', '.')
    return "generated/%s." % stock_path

def get_model(symbol, window_data, force=False):
    model_path = get_model_path(symbol)
    scaler_path = get_scaler_base_path(symbol)

    file_exists = exists(model_path)
    file_to_old = False

    if file_exists:
        file_to_old = is_file_older_than_x_days(model_path)

    if not force and file_exists and not file_to_old :
        return {
            'model': keras.models.load_model(model_path, compile=True), 
            'x_scaler': joblib.load(scaler_path + 'x_scaler'), 
            'y_scaler': joblib.load(scaler_path + 'y_scaler')
        }
    
    return create_model(symbol, model_path, scaler_path, window_data)

def create_model(symbol, model_path, scaler_path, window_data):
    df = window_data.copy().dropna()

    if df.empty or df.shape[0] < 100:
        print("%s has no data or not enough data to generate a model" % symbol)
        return None

    print(df)

    X = df.iloc[:, 0:-3]
    Y = df.iloc[:, -3:].to_numpy()

    x_scaler = RobustScaler()
    X = x_scaler.fit_transform(X)

    y_scaler = RobustScaler()
    Y = y_scaler.fit_transform(Y)

    split_data = int(len(df)*0.7)

    #X_train, X_test, Y_train, Y_test = X.iloc[:split_data, :], X.iloc[split_data:, :], Y.iloc[:split_data], Y.iloc[split_data:]
    X_train, X_test, Y_train, Y_test = X[:split_data, :], X[split_data:, :], Y[:split_data], Y[split_data:]

    X_train = X_train.reshape((1, X_train.shape[0], X_train.shape[1]))
    Y_train = Y_train.reshape((1, Y_train.shape[0], Y_train.shape[1]))

    print(X_train)

    #X_train = np.expand_dims(X_train, 1)

    model = tf.keras.Sequential([
        keras.layers.LSTM(128, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])),
        keras.layers.Dropout(0.46),
        keras.layers.LSTM(64, return_sequences=False),
        keras.layers.Dropout(0.44),
        keras.layers.Dense(3),
    ])

    model.compile(optimizer = 'adam', loss = 'mean_squared_error')

    model.fit(X_train, Y_train, batch_size = 125, epochs = 100)

    model.save(model_path)

    joblib.dump(x_scaler, scaler_path + 'x_scaler') 
    joblib.dump(y_scaler, scaler_path + 'y_scaler') 

    return {
        'model': model,
        'x_scaler': x_scaler,
        'y_scaler': y_scaler
    }
'''
    X_test = np.expand_dims(X_test, 1)
    Y_pred = model.predict(X_test)
    Y_pred = y_scaler.inverse_transform(Y_pred)

    for i in range(len(Y_test)):
        print("Close: T %s   P %s" % (Y_test[i,2], Y_pred[i][2]))
'''
