from helpers.buy import buy_symbol
from helpers.sell import sell_symbol
from helpers.trend_logic import predict_ewm
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

def sell_strat(loss_symbols, gain_symbols, trading_client, discord):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for p in current_positions:
        pl = float(p.unrealized_plpc)

        loss_p = next((s for s in loss_symbols if s['symbol'].replace("/", "") == p.symbol), None)
        gain_p = next((s for s in gain_symbols if s['symbol'].replace("/", "") == p.symbol), None)

        sell = False

        if pl > 0:
            # Profit, check if predicted to drop
            sell = loss_p != None
        else:
            # Loss, check if below limit and not predicted to gain
            sell = pl < -stop_loss or (pl < 0 and gain_p == None)

        # Two reasons to sell
        # 1 Profit + Predicted to drop
        # 2 Loss greater than limit and not predicted to gain

        if sell:
            sold = False
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

    for s in symbols:
        try:
            trend = predict_ewm(s, start, market_client)

            if trend == None:
                continue

            if trend['status'] == 'buy':
                buy.append({ 'symbol': s, 'trend': trend['trend'] })
            elif trend['status'] == 'sell':
                sell.append({ 'symbol': s, 'trend': trend['trend'] })

            if notify and trend['status'] != 'hold':
                current_ewm = "C Short: %s Long: %s" % (round(trend['current 10'], 2), round(trend['current 50'], 2))
                predicted_ewm = "P Short: %s Long: %s" % (round(trend['predicted 10'], 2), round(trend['predicted 50'], 2))
                closing_message = "Bar closing: $%s" % trend['current_close']
                rsi_message = "RSI: %s" % round(trend['rsi'], 2)
                volume_message = "Bar trade count: %s" % "{:,}".format(trend['trade_count'])
                discord.send("%s\n    %s\n    %s\n    %s\n    %s\n    %s\n    %s" % (s, current_ewm, predicted_ewm, closing_message, rsi_message, volume_message, trend['status']))
        except Exception as e:
            print(e)

    def trendSort(k):
        return k['trend']

    buy.sort(key=trendSort)
    sell.sort(key=trendSort)

    return { 'buy': buy, 'sell': sell }