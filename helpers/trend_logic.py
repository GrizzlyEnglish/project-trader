import numpy as np
from sklearn.preprocessing import StandardScaler
from alpaca.data.requests import  CryptoBarsRequest, StockBarsRequest
from alpaca.data import TimeFrame 
from datetime import datetime, timedelta
from alpaca.data.historical import CryptoHistoricalDataClient
from alpaca.common.exceptions import APIError

from helpers.generate_model import generate_model
from helpers.features import feature_engineer_df, get_percentage_diff

import math

def predict_ewm_12(symbol, full_bars, current_bars):
    model = generate_model(symbol, full_bars)

    df = feature_engineer_df(current_bars, False)

    predicted_price = 0

    scaler = StandardScaler()
    scaler.fit_transform(df)
    df_test = scaler.transform(df)
    df_test = np.expand_dims(df_test, 1)
    predicted = model.predict(df_test)
    predicted_price = predicted[0][0]

    if not math.isnan(predicted_price):
        percent_difference = get_percentage_diff(df['ewm_12'].iloc[0], predicted_price)
    else:
        percent_difference = 0

    print("     Start ewm_12 %s predicted ewm_12 %s, %s difference" % (df['ewm_12'].iloc[0], predicted_price, percent_difference))

    return { 
        'price': predicted_price, 
        'current': df['ewm_12'].iloc[0],  
        'difference': percent_difference ,
    }