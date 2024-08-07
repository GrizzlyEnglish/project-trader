from datetime import datetime, timedelta
from helpers import get_data, features

import os

# Steps
# 1. Get the last 1 hour of 1 min bars for symbol, get the ROC
# 2. Setup the amount of bars above/below 0
# 3. Get "strength" of call/put
# 4. If strong get cheapest ITM call/put
def enter(symbols, market_client, end = datetime.now()):
    enter = []
    for symbol in symbols:
        start = end - timedelta(days=1)
        bars = get_data.get_bars(symbol, start, end, market_client, 1)
        if bars.empty:
            continue

        bars = features.rate_of_change(bars)

        bars = bars.tail(60)

        power = bars['roc'].sum()
        c_power = bars[bars['roc'] > 0]['roc'].sum()
        p_power = bars[bars['roc'] < 0]['roc'].sum()
        print(f"{symbol} ROC power={power} call={c_power} put={p_power}")
        abs_p_power = abs(p_power)
        diff = abs(abs_p_power - c_power)
        if abs(power) > 8 and diff > 5:
            t = ""
            if abs_p_power > c_power:
                t = "put"
            elif abs_p_power < c_power:
                t = "call"
            
            if t != "":
                enter.append({
                    "symbol": symbol,
                    "type": t,
                    "price": bars["close"].iloc[-1]
                })
    return enter

# Sell if strength is flipped, -20% loss, or +30% gain
def exit(entries, positions):
    stop_loss = float(os.getenv('STOP_LOSS'))
    exits = []
    for position in positions:
        pl = float(position.unrealized_plpc)
        symbol = position.symbol

        entry = next((s for s in entries if symbol in s['symbol']), None)

        if pl < stop_loss or pl > .3:
            exit.append(symbol)
        elif entry != None:
            if 'C' in symbol[4:] and entry['type'] == 'P' or 'P' in symbol[4:] and entry['type'] == 'C':
                exit.append(symbol)

    return exit