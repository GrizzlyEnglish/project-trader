from dotenv import load_dotenv
from src.helpers import class_model, get_data, tracker, options, features
from src.strats import enter_option, exit_option
from src.classifiers import short
from datetime import datetime, timedelta

import ast
import os

load_dotenv()

def generate_short_models(market_client, end):
    symbols = ast.literal_eval(os.getenv('SYMBOLS'))
    day_diff = int(os.getenv('DAYDIFF'))

    models = []

    for symbol in symbols:
        print(f'--- {symbol} ---')
        model = class_model.generate_model(symbol, day_diff, market_client, short.classification, end)

        models.append({
            'symbol': symbol,
            'model': model['model']
        })

    return models

def classify(model, bars):
    c = class_model.classify(model, bars)
    if all(x == c[0] for x in c):
        return c[0]
    return 'Hold'

def do_enter(model, bars, symbol, positions):
    has_open_option = next((cp for cp in positions if symbol in cp.symbol), None) != None
    signal = classify(model, bars)
    return signal != 'Hold' and not has_open_option, signal

def do_exit(position, signals):
    secure_gains = int(os.getenv('SECURE_GAINS'))
    stop_loss = int(os.getenv('STOP_LOSS')) * -1

    pl = float(position.unrealized_plpc) * 100
    market_value = float(position.market_value)
    symbol = options.get_underlying_symbol(position.symbol)
    signal = next((s for s in signals if s['symbol'] == symbol), None)
    hst = tracker.get(position.symbol)

    print(f'{position.symbol} P/L % {pl} stop loss of {stop_loss} and secure gains of {secure_gains} current cost {market_value}')

    if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
        # Hold it we are signaling
        return False, ''

    if pl < secure_gains and not hst.empty and (hst['p/l'] > secure_gains).any():
        return True, 'secure gains' 
    
    if pl <= stop_loss:
        return True, 'stop loss'
    
    if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
        return True, 'reversal'
    
    #TODO: Determine how to sell when spook'd, and check for reversal
    if pl >= secure_gains and len(hst) > 6:
        last_slope = features.slope(hst.iloc[-3:]['market_value'])[0]
        last_two_slope = features.slope(hst.iloc[-6:-3]['market_value'])[0]
        if last_slope < last_two_slope:
            return True, 'secure gains'

    tracker.track(position.symbol, pl, market_value)

    return False, ''

def enter(models, market_client, trading_client, option_client):
    signals = []

    day_diff = int(os.getenv('DAYDIFF'))
    m_end = datetime.now() + timedelta(days=1)
    m_st = m_end - timedelta(days=day_diff)
    positions = get_data.get_positions(trading_client)

    for m in models:
        bars = get_data.get_model_bars(m['symbol'], market_client, m_st, m_end, 1, None, 'Min')
        b = bars[-1:]

        enter, signal = do_enter(m['model'], b, m['symbol'], positions)

        print(f'{m["symbol"]}: {b.index[0][1]} {signal}')

        if enter:
            signals.append({
                'symbol': m['symbol'],
                'signal': signal,
            })

    for c in signals:
        enter_option.enter(c, trading_client, market_client, option_client)
    
    return signals

def exit(signals, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    for p in positions:
        exit, reason = do_exit(p, signals)
        if exit:
            exit_option.exit(p, reason, trading_client)
            tracker.clear(p.symbol)
    return