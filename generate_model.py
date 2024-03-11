from alpaca.data.requests import StockBarsRequest
from datetime import datetime, timedelta
from alpaca.data import TimeFrame 
from sklearn.preprocessing import StandardScaler

import pandas as p
import numpy as np
import tensorflow as tf
from tensorflow import keras
from os.path import exists

def generate_model(stock, market_client):
    path = "generated/%s.model.keras" % stock

    if exists(path):
        model = keras.models.load_model(path, compile=True)
    else:
        window_start = datetime.now() - timedelta(days=30)
        window_end = datetime.now() 

        window_data = market_client.get_stock_bars(StockBarsRequest(symbol_or_symbols=stock,
                                start=window_start,
                                end=window_end,
                                adjustment='raw',
                                feed='sip',
                                timeframe=TimeFrame.Minute))
        
        df = window_data.df

        if df.empty:
            print("No data available for %s" % stock)

        df['ewm_12'] = df['close'].ewm(span=12, adjust=False).mean()
        df['ewm_24'] = df['close'].ewm(span=24, adjust=False).mean()

        future_ewm = []
        for i in range(len(df)):
            start_row = i
            end_row = min(i + 5, len(df))  
            subset = df.iloc[start_row:end_row]
            ewm_12_f = subset['ewm_12'].ewm(span=12, adjust=False).mean()
            future_ewm.append(ewm_12_f.iloc[-1])

        df.insert(9, 'ewm_12_f_2', future_ewm)

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
        model.fit(X_train, Y_train, batch_size = 500, epochs = 100)

        X_test = np.expand_dims(X_test, 1)
        Y_pred = model.predict(X_test)

        model.save(path)

    return model
'''
    for i in range(len(Y_test)):
        predicted = Y_pred[i][0]
        test = Y_test.iloc[i]
        percentage = abs(predicted - test) / ((predicted + test) / 2) * 100
        print(percentage)
'''