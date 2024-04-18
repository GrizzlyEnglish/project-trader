from helpers.buy import buy_symbol
from helpers.sell import sell_symbol
from helpers.trend_logic import predict_ewm_12
from helpers.get_data import get_bars
from helpers.features import rsi
from datetime import timedelta, datetime
from alpaca.trading.requests import GetOrdersRequest

import os

def sell_strat(type, symbols, trading_client, discord):
    current_positions = trading_client.get_all_positions()

    for p in current_positions:
        print("Current position on %s %s with a p/l of %s" % (p.symbol, p.qty, p.unrealized_pl))

        pl = float(p.unrealized_pl)

        s = next((s for s in symbols if s['symbol'].replace("/", "") == p.symbol), None)

        if s != None:
            if (pl > 0):
                sold = False
                if type == 'Crypto':
                    sold = True
                    sell_symbol(p, type, trading_client)
                else:
                    orders = trading_client.get_orders(GetOrdersRequest(after=datetime.now().replace(hour=9, minute=0, second=0, microsecond=0), symbols=p.symbol)) 
                    if len(orders) == 0:
                        sold = True
                        sell_symbol(p, type, trading_client)

                if sold:
                    discord.send("Selling %s it has a current P/L of %s and is expected to see a %s%% decrese in ewm" % (p.symbol, pl, s.trend))
            else:
                discord.send("%s has a current P/L of %s and is expected to see a %s%% decrese in ewm, check if it is worth selling at a loss or holding" % (p.symbol, pl, s.trend))

def buy_strat(symbols, trading_client, market_client, discord):
    account = trading_client.get_account()

    buying_power = float(account.buying_power)

    if buying_power > 0:
        for s in symbols:
            buy_symbol(s, trading_client, market_client, buying_power, discord)

            account = trading_client.get_account()

            buying_power = float(account.buying_power)

def filter_strat(symbol, market_client, start):
    volume_threshold = float(os.getenv('VOLUME_THRESHOLD'))

    week_bars = get_bars(symbol, start - timedelta(days=7), start, market_client)

    if week_bars.empty:
        return False

    volume = week_bars['volume'].sum()
    return volume > volume_threshold

def info_strat(symbols, market_client, discord, start):
    buy = []
    sell = []

    percentage_threshold = float(os.getenv('PREDICTED_THRESHOLD'))

    for s in symbols:
        try:
            trend = predict_ewm_12(s, start, market_client)

            if trend == None:
                continue

            over_threshold = False
            if trend['difference'] > percentage_threshold:
                buy.append(s)
                over_threshold = True
            elif trend['difference'] < -percentage_threshold:
                sell.append({ 'symbol': s, 'trend': trend['difference'] })
                over_threshold = True

            if over_threshold:
                prediction_message = "EMW prediction: %s%% at %s" % (trend['difference'], "${:,.2f}".format(trend['price']))
                closing_message = "Bar closing: $%s" % trend['current_close']
                rsi_message = "RSI: %s" % trend['rsi']
                volume_message = "Bar trade count: %s" % "{:,}".format(trend['trade_count'])
                discord.send("%s\n    %s\n    %s\n    %s\n    %s" % (s, prediction_message, closing_message, rsi_message, volume_message))
        except Exception as e:
            print(e)

    return { 'buy': buy, 'sell': sell }