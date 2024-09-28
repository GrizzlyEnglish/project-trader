from datetime import datetime
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers import get_data, class_model, get_data
from src.strats import enter
from src.helpers.load_parameters import load_symbol_parameters
from src.classifiers import runnup, dip

def generate_short_models(market_client, end):
    params = load_symbol_parameters('../params.json')

    models = []

    for p in params:
        symbol = p['symbol']
        runnup_model_info = class_model.generate_model(symbol, p['runnup'], market_client, runnup.classification, end)
        dip_model_info = class_model.generate_model(symbol, p['dip'], market_client, dip.classification, end)

        models.append({
            "dip": dip_model_info,
            "runnup": runnup_model_info,
            "symbol": symbol,
            "params": p
        })

    return models

def classify_short_signal(dip_bars, runnup_bars, model_info):
    dip_signal = class_model.predict(model_info['dip']['model'], dip_bars)[0]
    run_signals = class_model.predict(model_info['runnup']['model'], runnup_bars)

    signal = 'hold'
    # all runnups need to match, and dip just needs any of them
    if all(x == run_signals[0] for x in run_signals) and dip_signal == run_signals[0]:
        signal = run_signals[0]

    return {
        'runnup': run_signals,
        'dip': dip_signal,
        'signal': signal
    }


def enter_short(symbol_info, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    classifications = class_model.classify_symbols(symbol_info, runnup.classification, market_client, datetime.now(), TimeFrameUnit.Minute)

    for c in classifications:
        enter.enter_position(c, positions, trading_client, market_client, option_client)