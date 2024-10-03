from datetime import datetime
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers import get_data, class_model, get_data
from src.strats import enter
from src.helpers.load_parameters import load_symbol_parameters
from src.classifiers import runnup, dip, overnight

def generate_short_models(market_client, end, params_path = 'params.json'):
    params = load_symbol_parameters(params_path)

    models = []

    for p in params:
        symbol = p['symbol']
        print('RUNNUP Gen')
        runnup_model_info = class_model.generate_model(symbol, p['runnup'], market_client, runnup.classification, end)
        print('DIP Gen')
        dip_model_info = class_model.generate_model(symbol, p['dip'], market_client, dip.classification, end)
        print('OVERNIGHT Gen')
        overnight_model_info = class_model.generate_model(symbol, p['overnight'], market_client, overnight.classification, end)

        models.append({
            "dip": dip_model_info,
            "runnup": runnup_model_info,
            "overnight": overnight_model_info,
            "symbol": symbol,
            "params": p
        })

    return models

def classify_short_signal(dip_bars, runnup_bars, model_info):
    dip_signal = class_model.predict(model_info['dip']['model'], dip_bars)[0]
    run_signals = class_model.predict(model_info['runnup']['model'], runnup_bars)

    signal = 'Hold'
    # all runnups need to match, and dip just needs any of them
    if all(x == run_signals[0] for x in run_signals) and dip_signal == run_signals[0]:
        signal = run_signals[0]

    return {
        'runnup': run_signals,
        'dip': dip_signal,
        'signal': signal
    }

def classify_overnight_signal(overnight_bars, model_info):
    overnight_signal = class_model.predict(model_info['overnight']['model'], overnight_bars)[0]
    return overnight_signal

def enter_short(model_infos, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    classifications = []

    for m in model_infos:
        run_bars = class_model.get_prediction_bars(m['symbol'], m['params']['runnup'], market_client).iloc[-2:]
        dip_bars = class_model.get_prediction_bars(m['symbol'], m['params']['dip'], market_client)[:1]

        classif = classify_short_signal(dip_bars, run_bars, m)
        print(f'Dip: {classif["dip"]} Runnup: {classif["runnup"]} Signal: {classif["signal"]}')

        classifications.append({
            'symbol': m['symbol'],
            'class': classif['signal'],
            'call_variance': m['runnup']['call_variance'],
            'put_variance': m['runnup']['put_variance']
        })

    for c in classifications:
        enter.enter_position(c, positions, trading_client, market_client, option_client)