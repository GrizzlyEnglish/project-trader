import pandas as pd
from datetime import datetime

_TRACKING_PD = pd.DataFrame()

def track(symbol, pl):
    global _TRACKING_PD
    df = pd.DataFrame([[symbol, pl, datetime.now()]],columns=['symbol', 'p/l', 'timestamp'])
    _TRACKING_PD = pd.concat([_TRACKING_PD, df], ignore_index=True)

def get(symbol):
    global _TRACKING_PD
    if (_TRACKING_PD.empty): return _TRACKING_PD
    df = _TRACKING_PD[_TRACKING_PD['symbol'] == symbol]
    return df.sort_values(by='timestamp', ascending=False)

def clear(symbol):
    global _TRACKING_PD
    if (_TRACKING_PD.empty): return
    _TRACKING_PD = _TRACKING_PD.drop(_TRACKING_PD[_TRACKING_PD['symbol'] == symbol].index)