import numpy as np
import shapely.geometry as sg
import os
import math
import plotext as plt

from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
from helpers.get_data import get_bars

from helpers.generate_model import get_model, generate_model
from helpers.features import feature_engineer_df, get_percentage_diff

def predict_ewm(symbol, start, market_client, force=False, graph=False):
    if force:
        model = None
    else:
        model = get_model(symbol)

    days = float(os.getenv('FULL_DAY_COUNT'))
    full_bars = get_bars(symbol, start - timedelta(days=days), start, market_client)

    if full_bars.empty:
        return

    if model == None or force:
        model = generate_model(symbol, full_bars)

    clipped = 10

    df = feature_engineer_df(full_bars, False)
    df = df.tail(clipped)

    scaler = StandardScaler()
    scaler.fit_transform(df)
    df_test = scaler.transform(df)
    df_test = np.expand_dims(df_test, 1)
    predicted = model.predict(df_test)

    current_10_ewm = df['ewm_short']
    current_50_ewm = df['ewm_long']

    predicted_status = 'hold'

    shortLinePointsC = [(index, value) for index, value in enumerate(current_10_ewm)] 
    longLinePointsC = [(index, value) for index, value in enumerate(current_50_ewm)] 

    shortLinePointsP = [(index + clipped, value[0]) for index, value in enumerate(predicted)] 
    longLinePointsP = [(index + clipped, value[1]) for index, value in enumerate(predicted)] 

    sp = [item[1] for sublist in (shortLinePointsC, shortLinePointsP) for item in sublist]
    lp = [item[1] for sublist in (longLinePointsC, longLinePointsP) for item in sublist]

    shortEnd = sp[-1]
    longEnd = lp[-1]

    if graph:
        plt.plot(sp, label = "short")
        plt.plot(lp, label = "long")

        plt.title("%s" % symbol)
        plt.show()

    shortPoints = [item for sublist in (shortLinePointsC, shortLinePointsP) for item in sublist] 
    shortline = sg.LineString(shortPoints)

    longPoints = [item for sublist in (longLinePointsC, longLinePointsP) for item in sublist] 
    longline = sg.LineString(longPoints)

    if shortline.intersects(longline):
        if shortEnd > longEnd:
            predicted_status = 'buy'
        else:
            predicted_status = 'sell'

    print("  C Short: %s Long: %s  P Short: %s Long: %s    Status: %s" % (current_10_ewm.iloc[-1], current_50_ewm.iloc[-1], shortEnd, longEnd, predicted_status))

    return { 
        'status': predicted_status,
        'current 10': df['ewm_short'].iloc[0],  
        'current 50': df['ewm_long'].iloc[0],  
        'predicted 10': shortEnd,  
        'predicted 50': longEnd,  
        'trend': longEnd - df['ewm_long'].iloc[0],
        'close': df.iloc[-1]['close'],
        'rsi': df.iloc[-1]['rsi'],
        'current_close': full_bars.iloc[-1]['close'],
        'trade_count': full_bars.iloc[-1]['trade_count']
    }