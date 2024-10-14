from dotenv import load_dotenv
from src.helpers import class_model, get_data
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

def do_enter(model, bars):
    signal = classify(model, bars)
    #TODO: Do any logic here? Or just enter
    return signal != 'Hold', signal

def do_exit(position):
    secure_gains = int(os.getenv('SECURE_GAINS'))
    stop_loss = int(os.getenv('STOP_LOSS'))

    pl = float(position.unrealized_plpc)
    market_value = float(position.market_value)

    print(f'{position.symbol} P/L % {pl} stop loss of {stop_loss} and secure gains of {secure_gains} current cost {market_value}')

    if pl >= secure_gains:
        return True, 'secure gains' 
    
    if pl <= stop_loss:
        return True, 'stop loss'
    
    #TODO: Determine how to sell when spook'd, and check for reversal

    return

def enter(models, market_client, trading_client, option_client):
    signals = []

    day_diff = int(os.getenv('DAYDIFF'))
    m_end = datetime.now()
    m_st = m_end - timedelta(days=day_diff)

    for m in models:
        bars = get_data.get_model_bars(m['symbol'], market_client, m_st, m_end, 1, None, 'Min')[-1:]

        enter, signal = do_enter(m['model'], bars)

        print(f'{m["symbol"]}: {bars.index[0][1]} {signal}')

        if enter:
            signals.append({
                'symbol': m['symbol'],
                'signal': signal,
            })

    for c in signals:
        enter_option.enter(c, trading_client, market_client, option_client)

def exit(models, market_client, trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    for p in positions:
        exit, reason = do_exit(p)
        if exit:
            exit_option.exit(p, reason, trading_client)
    return