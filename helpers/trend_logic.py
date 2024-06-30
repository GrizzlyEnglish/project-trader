import numpy as np
import shapely.geometry as sg
import plotext as plt

from helpers.rnn_model import get_prediction
from helpers.get_data import get_bars
from helpers.get_data import get_bars
from helpers.features import feature_engineer_df, fully_feature_engineer 
from datetime import timedelta, datetime
from sklearn.preprocessing import MinMaxScaler 

import os

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

def current_status(s, full_bars):
    graph = (os.getenv('GRAPH_CROSSOVERS', 'False') == 'True')

    df = full_bars.copy().tail(40)

    crossover_status = crossover_trend(df['ma_short'].tail(15), df['ma_long'].tail(15), graph)

    macd_status = macd_trend(df['macd'], df['signal'], graph)
    obv_status = obv_trend(df)
    rsi_status = rsi_trend(df)

    print("[%s] MA %s S: %s L: %s | MACD %s M: %s S: %s | RSI %s %s | OBV %s %s" % (
        s,
        crossover_status,
        round(df['ma_short'].iloc[-1], 2),
        round(df['ma_long'].iloc[-1], 2),
        macd_status,
        round(df['macd'].iloc[-1], 2),
        round(df['signal'].iloc[-1], 2),
        rsi_status,
        round(df['rsi'].iloc[-1], 2),
        obv_status,
        round(df['obv'].iloc[-1], 2),
    ))

    return {
        'rsi': rsi_status,
        'macd': macd_status,
        'obv': obv_status,
        'cross': crossover_status
    }

def weight_symbol_current_status(symbols, market_client, start):
    marked_symbols = []
    days = float(os.getenv('CURRENT_DAY_COUNT'))
    until = start - timedelta(days=days)
    for s in symbols:
        try:
            full_bars = get_bars(s, until, start, market_client)

            if full_bars.empty:
                continue

            full_bars = feature_engineer_df(full_bars)

            current_stats = current_status(s, full_bars)

            weight = 0
            weight += get_buy_sell_weight(current_stats['cross'], 7)
            weight += get_buy_sell_weight(current_stats['rsi'], 4)
            weight += get_buy_sell_weight(current_stats['macd'], 3)
            weight += get_buy_sell_weight(current_stats['obv'], 2)

            marked_symbols.append({ 
                'symbol': s, 
                'weight': weight,
                'abs_weight': abs(weight),
                'last_close': full_bars['close'].iloc[-1],
                'volume': full_bars['volume'].sum()
            })
        except Exception as e:
            print(e)

    return marked_symbols

def get_predicted_price(symbol, market_client, end=None):
    prediction = predict_status(symbol, market_client, end)
    if prediction == None:
        return None
    return prediction['predicted_close']

def predict_status(symbol, market_client, end=None):
    graph = os.getenv('GRAPH_CROSSOVERS') == 'True'
    force_model = os.getenv('FORCE_MODEL_GEN') == 'True'
    days = float(os.getenv('PREDICT_DAY_COUNT'))

    if end == None:
        end = datetime.now()

    start = end - timedelta(days=days)

    full_bars = get_bars(symbol, start, end, market_client)

    full_bars = fully_feature_engineer(full_bars)

    current_close = full_bars.iloc[-1]['close']
    current_short = full_bars['ma_short'].iloc[0]
    current_long = full_bars['ma_short'].iloc[0]

    short_points, long_points, future_close = get_prediction(symbol, full_bars, force_model)

    if short_points == None or long_points == None or future_close == None:
        return None

    crossed = cross_line(short_points, long_points, 'PREDICTED MA', graph)
    predicted_cross_status = cross_line_status(crossed)

    avg_future = round(np.average(np.array(future_close)),2) 
    predicted_price_status = price_based_status(current_close, avg_future)

    print("  Predicted Short: %s Long: %s    Status: %s" % (short_points[-1], long_points[-1], predicted_cross_status))
    print("  Predicted Price: %s Current Price: %s    Status: %s" % (avg_future, current_close, predicted_price_status))

    return { 
        'predicted_cross': predicted_cross_status,
        'current_short': current_short,  
        'current_long': current_long,  
        'current_close': current_close,
        'predicted_short': short_points[-1],  
        'predicted_long': long_points[-1],
        'predicted_close': avg_future,
        'predicted_price': predicted_price_status
    }

def get_buy_sell_weight(status, scale):
    if status == "buy":
        return scale
    elif status == "sell":
        return scale * -1
    return 0