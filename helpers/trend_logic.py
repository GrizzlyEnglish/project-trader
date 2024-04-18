import numpy as np
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from helpers.get_data import get_bars

from helpers.generate_model import get_model, generate_model
from helpers.features import feature_engineer_df, get_percentage_diff

import os
import math

def predict_ewm_12(symbol, start, market_client):
    model = get_model(symbol)

    if model == None:
        days = float(os.getenv('FULL_DAY_COUNT'))
        full_bars = get_bars(symbol, start - timedelta(days=days), start, market_client)
        if full_bars.empty:
            return
        model = generate_model(symbol, full_bars)

    current_bars = get_bars(symbol, start - timedelta(days=4), start, market_client)
    current_bars = current_bars.tail(20)

    if current_bars.empty:
        return
    
    df = feature_engineer_df(current_bars, False)

    df = df.tail(1)

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
        'difference': percent_difference,
        'close': df.iloc[-1]['close'],
        'rsi': df.iloc[-1]['rsi'],
        'current_close': current_bars.iloc[-1]['close'],
        'trade_count': current_bars.iloc[-1]['trade_count']
    }