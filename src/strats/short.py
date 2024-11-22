from dotenv import load_dotenv
from src.helpers import class_model, get_data, tracker, options, features
from src.strats import enter_option, exit_option
from src.classifiers import trending
from datetime import datetime, timedelta

import ast
import os
import math
import numpy as np

load_dotenv()

def generate_short_models(market_client, end):
    symbols = ast.literal_eval(os.getenv('SYMBOLS'))
    day_diff = int(os.getenv('DAYDIFF'))

    models = []

    m_st = end - timedelta(days=day_diff-1)
    m_end = end

    for symbol in symbols:
        print(f'--- {symbol} ---')

        m_st = m_st.replace(hour=1, minute=0, second=0)
        m_end = m_end.replace(hour=23, minute=59, second=59)

        bars = get_data.get_bars(symbol, m_st, m_end, market_client, 1, 'Min')
        bars = features.feature_engineer_df(bars)

        print(f'Model start {m_st} model end {m_end} with bar counr of {len(bars)}')
        tmodel = class_model.generate_model(symbol, bars, trending.classification)

        models.append({
            'symbol': symbol,
            'model': {
                #'barrier': bmodel['model'],
                'trend': tmodel['model'],
            } 
        })

    return models

def classify(model, bars):
    predicitons = class_model.classify(model, bars)
    predicitons = np.array(predicitons)
    if np.all(predicitons == predicitons[0]):
        return predicitons[0]

    return 'Hold'

def do_enter(model, bar, symbol, positions, indicator):
    if indicator == 0:
        return False, 'Hold'
    has_open_option = next((cp for cp in positions if symbol in cp.symbol), None) != None
    if has_open_option:
        return False, 'Hold'

    signal = classify(model, bar)
    print(f'signal {signal} indicator {indicator}')
    if signal == 'Buy' and indicator == 1 or signal == 'Sell' and indicator == -1:
        return True, signal

    return False, 'Hold'

def do_exit(position, signals):
    symbol = options.get_underlying_symbol(position.symbol)
    risk = int(os.getenv(f'{symbol}_RISK'))
    reward_scale = int(os.getenv(f'{symbol}_REWARD_SCALE'))

    pl = float(position.unrealized_plpc) * 100
    cost = float(position.cost_basis)
    qty = float(position.qty)
    market_value = float(position.market_value)
    symbol_signal = next((s for s in signals if s['symbol'] == symbol), None)
    signal = 'Hold'
    if symbol_signal != None:
        signal = symbol_signal['signal']
    hst = tracker.get(position.symbol)

    # Determine the actual amount we are risking, and how much to gain
    risk = min(cost, risk*qty)
    reward = risk * reward_scale

    secure_gains = math.floor(cost + reward)
    stop_loss = math.floor(cost - risk)

    print(f'{position.symbol} P/L % {pl} {stop_loss}/{secure_gains} current: {market_value} bought: {cost} signal: {signal}')

    if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
        # Hold it we are signaling
        return False, ''
    
    passed_secure_gains = not hst.empty and (hst['market_value'] >= secure_gains).any()
    if passed_secure_gains:
        if market_value <= (secure_gains + 1):
            return True, 'secure gains' 

        idx = hst.index[hst['market_value'] >= secure_gains][0]
        sub_hst = hst.iloc[idx:]['market_value']
        if len(sub_hst) > 3:
            slope = features.slope(sub_hst[:-2])[0] if len(sub_hst) > 3 else 0
            slope_next = features.slope(sub_hst[:-1])[0] if len(sub_hst) > 3 else 0
            slope_next_next = features.slope(sub_hst)[0] if len(sub_hst) > 3 else 0
            if slope > slope_next > slope_next_next:
                return True, 'secure gains' 
            
    if pl < 0 and len(hst) > 5 and stop_loss > 75:
        slope = features.slope(hst['market_value'])[0] if len(hst) > 3 else 0
        if slope < -.5:
            return True, 'stop loss with slope'

    if market_value <= stop_loss:
        return True, 'stop loss'
    
    if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
        return True, 'reversal'
    
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
        close = bars.iloc[-1]['close'] 
        time = bars[-1:].index[0][1]
        indicator = bars.iloc[-1]['indicator']

        bars = class_model.preprocess_bars(bars)
        b = bars[-1:]

        enter, signal = do_enter(m['model'], b, m['symbol'], positions)

        print(f'{m["symbol"]}: {time} {signal}')

        if enter:
            c = {
                'symbol': m['symbol'],
                'signal': signal,
            }
            signals.append(c)
            enter_option.enter(c, close, trading_client, option_client)

    return signals

def exit(signals, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    for p in positions:
        exit, reason = do_exit(p, signals)
        if exit:
            print(f'Exiting {p.symbol} due to {reason}')
            exit_option.exit(p, reason, trading_client)
            tracker.clear(p.symbol)
    return