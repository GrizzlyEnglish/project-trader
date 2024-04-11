from helpers.buy import buy_symbol
from helpers.sell import sell_symbol
from helpers.trend_logic import predict_ewm_12
from helpers.get_data import get_bars
from helpers.features import rsi
from datetime import timedelta

def sell_strat(symbols, trading_client, discord):
    current_positions = trading_client.get_all_positions()

    for p in current_positions:
        print("Current position on %s %s with a p/l of %s" % (p.symbol, p.qty, p.unrealized_pl))

        pl = float(p.unrealized_pl)

        s = next((s for s in symbols if s.symbol == p.symbol), None)

        if (pl > 0 and s != None):
            discord.send("[%s] Selling %s it has a current P/L of %s and is expected to see a %s%% decrese in ewm" % (type, p.symbol, pl, s.trend))
            sell_symbol(p.symbol, trading_client)
        else:
            discord.send("[%s] %s has a current P/L of %s and is expected to see a %s%% decrese in ewm, check if it is worth selling at a loss or holding" % (type, p.symbol, pl, s.trend))

def buy_strat(symbols, trading_client, market_client, discord):
    account = trading_client.get_account()

    buying_power = float(account.buying_power)

    if buying_power > 0:
        for s in symbols:
            buy_symbol(s, trading_client, market_client, buying_power, discord)

            account = trading_client.get_account()

            buying_power = float(account.buying_power)

def info_strat(type, symbols, market_client, discord, start):
    buy = []
    sell = []
    days = 60
    mins = 5

    percentage_threshold = 10
    volume_threshold = 1000000

    for s in symbols:
        full_bars = get_bars(s, start - timedelta(days=days), start - timedelta(minutes=mins), market_client)
        current_bars = get_bars(s, start - timedelta(minutes=mins), start, market_client)

        if current_bars.empty or full_bars.empty:
            continue

        if current_bars.iloc[-1]['close'] < full_bars['close'].min():
            discord.send("%s just closed at its lowest in %s days at %s" % (type, s, days, current_bars.iloc[-1]['close']))

        trend = predict_ewm_12(s, full_bars, current_bars)

        if trend == None:
            continue

        week_bars = get_bars(s, start - timedelta(days=7), start, market_client)
        volume = week_bars['volume'].sum()

        if volume > volume_threshold:
            over_threshold = False
            if trend['difference'] > percentage_threshold:
                buy.append(s)
                over_threshold = True
            elif trend['difference'] < -percentage_threshold:
                sell.append({ 'symbol': s, 'trend': trend['difference'] })
                over_threshold = True

            if over_threshold:
                discord.send("%s \n   EMW Prediction: %s%% \n   Closing: $%s \n   RSI: %s \n   Volume 7/d: %s" % (s, trend['difference'], trend['close'], trend['rsi'], "{:,}".format(volume)))

    return { 'buy': buy, 'sell': sell }