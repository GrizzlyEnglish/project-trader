import numpy as np
import shapely.geometry as sg
import plotext as plt

from sklearn.preprocessing import StandardScaler
from helpers.generate_model import get_model
from helpers.features import obv, rsi, feature_engineer_df

def cross_line(pA, pB, name, graph):
    aPoints = [(index, value) for index, value in enumerate(pA)] 
    bPoints = [(index, value) for index, value in enumerate(pB)] 

    aline = sg.LineString(aPoints)
    bline = sg.LineString(bPoints)

    aEnd = aPoints[-1][1]
    bEnd = bPoints[-1][1]

    if graph:
        sp = [item[1] for item in aPoints]
        lp = [item[1] for item in bPoints]

        plt.plot(sp, label = "short")
        plt.plot(lp, label = "long")

        plt.title(name)
        plt.show()

        plt.clear_data()

    if bline.intersects(aline):
        if bEnd > aEnd:
            return 'b'
        else:
            return 'a'

    return None

def cross_line_status(crossed):
    if crossed == 'a':
        return 'buy'
    elif crossed == 'b':
        return 'sell'

    return 'hold'

def price_based_status(current, predicted):
    if predicted > current:
        return 'buy'
    elif predicted < current:
        return 'sell'

    return 'hold'

def crossover_trend(short, long, graph):
    crossed = cross_line(short, long, 'CROSSOVER', graph)
    return cross_line_status(crossed)

def macd_trend(macd, signal, graph):
    crossed = cross_line(macd, signal, 'MACD', graph)
    return cross_line_status(crossed)

def obv_trend(df):
    #obv_df = obv(df)
    obv_df = df['obv']
    trend = obv_df.pct_change()

    trend_up = trend[trend > 0.01].shape[0]
    trend_down = trend[trend < -0.01].shape[0]
    trend_stale = trend.count() - (trend_up + trend_down)

    if trend_up > (trend_down + trend_stale):
        return 'buy'
    elif trend_stale > (trend_up + trend_down) or trend_down > trend_up:
        return 'sell'

    return 'hold'

def rsi_trend(df):
    bullish = len(df[df['rsi'] < 30]) > 0 and len(df[df['rsi'] > 30]) > 0
    bearish = len(df[df['rsi'] > 70]) > 0 and len(df[df['rsi'] > 70]) > 0

    if bullish:
        return 'buy'
    elif bearish:
        return 'sell'

    return 'hold'

def current_status(full_bars, graph):
    df = full_bars.copy().tail(40)

    crossover_status = crossover_trend(df['ma_short'].tail(15), df['ma_long'].tail(15), graph)
    print("  Crossover Short: %s Long: %s    Status: %s" % (df['ma_short'].iloc[-1], df['ma_long'].iloc[-1], crossover_status))

    df = feature_engineer_df(df)

    macd_status = macd_trend(df['macd'], df['signal'], graph)
    print("  MACD macd: %s signal: %s    Status: %s" % (df['macd'].iloc[-1], df['signal'].iloc[-1], macd_status))

    obv_status = obv_trend(df)
    print("  OBV Status: %s" % obv_status)

    rsi_status = rsi_trend(df)
    print("  RSI Status: %s" % rsi_status)

    return {
        'rsi': rsi_status,
        'macd': macd_status,
        'obv': obv_status,
        'cross': crossover_status
    }

def predict_status(symbol, full_bars, forceModel, graph=False):
    model = get_model(symbol, full_bars, forceModel)

    clipped = 20

    df = full_bars.copy().dropna().tail(clipped)

    # Values to predict
    df.drop('ma_short_f_2', axis=1, inplace=True)
    df.drop('ma_long_f_2', axis=1, inplace=True)
    df.drop('future_close', axis=1, inplace=True)

    scaler = StandardScaler()
    scaler.fit_transform(df)
    df_test = scaler.transform(df)
    df_test = np.expand_dims(df_test, 1)
    predicted = model.predict(df_test)

    shortPoints = [value[1][0] for value in enumerate(predicted)] 
    longPoints = [value[1][1] for value in enumerate(predicted)] 
    future_close = [value[1][2] for value in enumerate(predicted)] 

    crossed = cross_line(shortPoints, longPoints, 'PREDICTED MA', graph)
    predicted_cross_status = cross_line_status(crossed)

    avg_future = round(np.average(np.array(future_close)),2) 
    current_close = df.iloc[-1]['close']
    predicted_price_status = price_based_status(current_close, avg_future)

    print("  Predicted Short: %s Long: %s    Status: %s" % (shortPoints[-1], longPoints[-1], predicted_cross_status))
    print("  Predicted Price: %s Current Price: %s    Status: %s" % (current_close, avg_future, predicted_price_status))

    return { 
        'predicted_cross': predicted_cross_status,
        'current_short': df['ma_short'].iloc[0],  
        'current_long': df['ma_long'].iloc[0],  
        'predicted_short': shortPoints[-1],  
        'predicted_long': longPoints[-1],
        'future_close': avg_future,
        'predicted_price': predicted_price_status
    }