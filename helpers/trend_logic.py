import numpy as np
from sklearn.preprocessing import StandardScaler
from alpaca.data.requests import CryptoLatestBarRequest, CryptoBarsRequest
from alpaca.data import TimeFrame 
from datetime import datetime, timedelta
import pandas as pd

from helpers.generate_model import generate_model
from helpers.features import feature_engineer_df, get_percentage_diff

def predict_ewm_12(coin, crypto_market_client):
    if "/USD" not in coin:
        coin = coin.replace("USD", "/USD")

    full_data = crypto_market_client.get_crypto_bars(CryptoBarsRequest(symbol_or_symbols=coin,
                            start=datetime.now() - timedelta(days=30),
                            end=datetime.now() - timedelta(minutes=5),
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame.Minute))

    model = generate_model(coin, full_data.df)

    # Get current window to see what it is selling for
    current_bars = crypto_market_client.get_crypto_bars(CryptoBarsRequest(symbol_or_symbols=coin,
                            start=datetime.now() - timedelta(minutes=5),
                            end=datetime.now(),
                            adjustment='raw',
                            feed='sip',
                            timeframe=TimeFrame.Minute))

    df = feature_engineer_df(current_bars.df, False)

    predicted_price = 0

    scaler = StandardScaler()
    scaler.fit_transform(df)
    df_test = scaler.transform(df)
    df_test = np.expand_dims(df_test, 1)
    predicted = model.predict(df_test)
    predicted_price = predicted[0][0]
    percent_difference = get_percentage_diff(df['ewm_12'].iloc[0], predicted_price)

    print("     Start ewm_12 %s predicted ewm_12 %s, %s difference" % (df['ewm_12'].iloc[0], predicted_price, percent_difference))

    return { 'price': predicted_price, 'current': df['ewm_12'].iloc[0],  'difference': percent_difference }