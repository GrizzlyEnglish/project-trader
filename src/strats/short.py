from dotenv import load_dotenv
from src.helpers import class_model, get_data, tracker, options, features
from src.strats import enter_option, exit_option
from src.classifiers import dip, barrier, trending
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

        bars = get_data.get_bars(symbol, m_st, m_end, market_client, 1, 'Min')
        bars = features.feature_engineer_df(bars)

        print(f'Model start {m_st} model end {m_end} with bar counr of {len(bars)}')
        print('Barrier')
        rmodel = class_model.generate_model(symbol, bars, barrier.classification)
        print('Dip')
        dmodel = class_model.generate_model(symbol, bars, dip.classification)
        print('Trending')
        tmodel = class_model.generate_model(symbol, bars, trending.classification)

        models.append({
            'symbol': symbol,
            'model': {
                'runnup': rmodel['model'],
                'dip': dmodel['model'],
                'trend': tmodel['model'],
            } 
        })

    return models

def classify(model, bars):
    predicitons = class_model.classify(model, bars)
    predicitons = np.array(predicitons)
    if np.all(predicitons == predicitons[0]):
        return predicitons[0]
    else:
        return 'Hold'

def do_enter(model, bars, symbol, positions):
    has_open_option = next((cp for cp in positions if symbol in cp.symbol), None) != None
    signal = classify(model, bars)
    return signal != 'Hold' and not has_open_option, signal

def do_exit(position, signals):
    risk = int(os.getenv('RISK'))
    reward_scale = int(os.getenv('REWARD_SCALE'))
    runnup = int(os.getenv('RUNNUP'))

    pl = float(position.unrealized_plpc) * 100
    cost = float(position.cost_basis)
    qty = float(position.qty)
    market_value = float(position.market_value)
    symbol = options.get_underlying_symbol(position.symbol)
    symbol_signal = next((s for s in signals if s['symbol'] == symbol), None)
    signal = 'Hold'
    if symbol_signal != None:
        signal = symbol_signal['signal']
    hst = tracker.get(position.symbol)

    # Determine the actual amount we are risking, and how much to gain
    risk = min(cost, risk*qty)
    reward = risk * reward_scale

    secure_gains = cost + reward
    secure_limit = cost + math.ceil(reward/2)
    stop_loss = cost - risk

    print(f'{position.symbol} P/L % {pl} {stop_loss}/{secure_gains} current: {market_value} bought: {cost} signal: {signal}')

    if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
        # Hold it we are signaling
        return False, ''
    
    #if not hst.empty and ((datetime.now () - hst.iloc[0]['timestamp']) > timedelta(minutes=runnup)) and pl < 0:
        #return True, 'held too long'

    if market_value > secure_gains:
        return True, 'secure gains' 
    
    if market_value <= stop_loss:
        return True, 'stop loss'
    
    if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
        return True, 'reversal'

    #if market_value <= secure_limit and not hst.empty and (hst['market_value'] > secure_limit).any():
        #return True, 'secure limit' 
    
    #TODO: Determine how to sell when spook'd, and check for reversal
    if market_value >= secure_limit and len(hst) > 20:
        last_slope = features.slope(hst.iloc[-10:]['market_value'])[0]
        last_two_slope = features.slope(hst.iloc[-20:-10]['market_value'])[0]
        if last_slope < 0 or last_slope < (last_two_slope/2):
            return True, f'secure limit slope {last_slope}/{last_two_slope}'

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
            c = {
                'symbol': m['symbol'],
                'signal': signal,
            }
            signals.append(c)
            enter_option.enter(c, b.iloc[0]['close'], trading_client, option_client)

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