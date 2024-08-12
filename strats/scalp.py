from datetime import datetime, timedelta
from helpers import get_data, features

import os

def get_roc_power(symbol, start, end, market_client):
    bars = get_data.get_bars(symbol, start, end, market_client, 1)
    if bars.empty:
        return None

    bars = features.rate_of_change(bars)

    bars = bars.tail(60)

    power = bars['roc'].sum()

    # Determine if recently there was a configured amount of bars that were + or -, getting their power

    print(f"{symbol} ROC power={power} ")

    return {
        'power': power,
        'close': bars["close"].iloc[-1]
    }

# Steps
# 1. Get the last 1 hour of 1 min bars for symbol, get the ROC
# 2. Setup the amount of bars above/below 0
# 3. Get "strength" of call/put
# 4. If strong get cheapest ITM call/put
def enter(symbols, market_client, end = datetime.now()):
    enter = []
    for symbol in symbols:
        start = end - timedelta(days=1)

        roc_power = get_roc_power(symbol, start, end, market_client)

        diff = roc_power['diff']
        power = roc_power['power']
        close = roc_power['close']

        t = ""
        if diff > 75:
            if power > 10:
                t = "call"
            elif power < -10:
                t = "put"

        if t != "":
            enter.append({
                "symbol": symbol,
                "type": t,
                "price": close
            })
    return enter

# Sell if strength is flipped, -20% loss, or +30% gain
def exit(positions, symbols, end, market_client):
    stop_loss = float(os.getenv('STOP_LOSS'))
    secure_gains = float(os.getenv('SECURE_GAINS'))
    exits = []
    for position in positions:
        pl = float(position.unrealized_plpc)
        contract = position.symbol
        symbol = next((s for s in symbols if s in contract), None)

        print(f'{symbol} P/L % {pl}')

        if pl < -stop_loss: 
            exits.append(contract)
        else:
            start = end - timedelta(days=1)

            roc_power = get_roc_power(symbol, start, end, market_client)

            c_power = roc_power['c_power']
            p_power = roc_power['p_power']

            if 'C' in symbol:
                if c_power < 15 and pl > secure_gains or c_power < 10:
                    exits.append(contract)
            elif 'P' in symbol:
                if p_power < -15 and pl > secure_gains or c_power < -10:
                    exits.append(contract)

    return exits