from helpers.buy import buy_symbol
from helpers.sell import sell_symbol
from helpers.trend_logic import predict_ewm_12
from helpers.get_data import get_bars
from helpers.generate_model import generate_model
from datetime import timedelta, datetime
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange

import os

def fully_generate_all_stocks(trading_client, stock_market_client, start):
    request = GetAssetsRequest(asset_class=AssetClass.US_EQUITY, status=AssetStatus.ACTIVE, exchange=AssetExchange.NYSE)
    response = trading_client.get_all_assets(request)
    stocks = [s.symbol for s in response if filter_strat(s.symbol, stock_market_client, start)]

    days = float(os.getenv('FULL_DAY_COUNT'))

    print(len(stocks))

    for s in stocks:
        try:
            full_bars = get_bars(s, start - timedelta(days=days), start, stock_market_client)
            generate_model(s, full_bars)
        except Exception as e:
            print(e)

def sell_strat(type, symbols, trading_client, discord):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for p in current_positions:
        pl = float(p.unrealized_plpc)

        s = next((s for s in symbols if s['symbol'].replace("/", "") == p.symbol), None)

        if s != None or pl < -stop_loss:
            sold = False
            if type == 'Crypto':
                sold = True
                sell_symbol(p, type, trading_client)
            else:
                try:
                    orders = trading_client.get_orders(GetOrdersRequest(after=datetime.now().replace(day=1, hour=1, minute=0, second=0, microsecond=0), symbols=[p.symbol])) 
                    if len(orders) == 0:
                        sell_symbol(p, type, trading_client)
                        sold = True
                except Exception as e:
                    print(e)
                    discord.send("[Sell] Failed to sell %s 'cause %s" % (p.symbol, e))

            if sold:
                discord.send("[Sell] %s" % p.symbol)

def buy_strat(symbols, trading_client, market_client, discord):
    account = trading_client.get_account()

    buying_power = float(account.buying_power)

    if buying_power > 0:
        for s in symbols:
            bought = buy_symbol(s['symbol'], trading_client, market_client, buying_power, discord)

            if bought:
                discord.send("[Buy] %s with %s trending at %s" % (s['symbol'], buying_power, s['trend']))

            account = trading_client.get_account()

            buying_power = float(account.buying_power)

def filter_strat(symbol, market_client, start):
    volume_threshold = float(os.getenv('VOLUME_THRESHOLD'))

    week_bars = get_bars(symbol, start - timedelta(days=7), start, market_client)

    if week_bars.empty:
        return False

    volume = week_bars['volume'].sum()
    return volume > volume_threshold

def info_strat(symbols, market_client, discord, start, notify):
    buy = []
    sell = []

    percentage_threshold = float(os.getenv('PREDICTED_THRESHOLD'))

    for s in symbols:
        try:
            trend = predict_ewm_12(s, start, market_client)

            if trend == None:
                continue

            over_threshold = False
            if trend['difference'] > 0:
                buy.append({ 'symbol': s, 'trend': trend['difference'] })
                over_threshold = trend['difference'] > percentage_threshold
            elif trend['difference'] < 0:
                sell.append({ 'symbol': s, 'trend': trend['difference'] })
                over_threshold = trend['difference'] < -percentage_threshold

            if over_threshold and notify:
                prediction_message = "EMW prediction: %s%% at %s" % (trend['difference'], "${:,.2f}".format(trend['price']))
                closing_message = "Bar closing: $%s" % trend['current_close']
                rsi_message = "RSI: %s" % trend['rsi']
                volume_message = "Bar trade count: %s" % "{:,}".format(trend['trade_count'])
                discord.send("%s\n    %s\n    %s\n    %s\n    %s" % (s, prediction_message, closing_message, rsi_message, volume_message))
        except Exception as e:
            print(e)

    def trendSort(k):
        return k['trend'] * -1

    buy.sort(key=trendSort)
    sell.sort(key=trendSort)

    return { 'buy': buy, 'sell': sell }