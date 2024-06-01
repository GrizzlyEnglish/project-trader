from helpers.buy import buy_symbol
from helpers.sell import sell_symbol
from helpers.trend_logic import predict_status, current_status
from helpers.get_data import get_bars
from helpers.generate_model import get_model
from helpers.features import feature_engineer_df
from datetime import timedelta, datetime
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus, AssetExchange, OrderSide
from discord_webhook import DiscordEmbed, DiscordWebhook

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
            get_model(s, full_bars, True)
        except Exception as e:
            print(e)

def sell_strat(loss_symbols, gain_symbols, trading_client):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for p in current_positions:
        pl = float(p.unrealized_plpc)

        loss_p = next((s for s in loss_symbols if s['symbol'].replace("/", "") == p.symbol), None)
        gain_p = next((s for s in gain_symbols if s['symbol'].replace("/", "") == p.symbol), None)

        sell = False

        if pl > 0:
            # Profit, check if predicted to drop
            sell = loss_p != None or gain_p == None
        else:
            # Loss, check if below limit and not predicted to gain
            sell = pl < -stop_loss or (pl < 0 and gain_p == None) or loss_p != None

        # Two reasons to sell
        # 1 Profit + Predicted to drop
        # 2 Loss greater than limit and not predicted to gain

        if sell:
            try:
                previous_date = datetime.now() - timedelta(hours=12)
                orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=OrderSide.BUY, symbols=[p.symbol])) 
                if len(orders) == 0:
                    sell_symbol(p, trading_client)
                    sendAlpacaMessage("[Sell] Sold %s" % p.symbol)
                else:
                    sendAlpacaMessage("[Sell] Did not sell %s had a buy within 24 hours" % p.symbol)
            except Exception as e:
                print(e)
                sendAlpacaMessage("[Sell] Failed to sell %s 'cause %s" % (p.symbol, e))
        else:
            sendAlpacaMessage("[Sell] Did not sell %s with p/l of %s (gain: %s loss: %s)" % (p.symbol, pl, loss_p != None, gain_p != None))

def buy_strat(symbols, trading_client, market_client,):
    account = trading_client.get_account()

    buying_power = float(account.buying_power)

    if buying_power > 0:
        for s in symbols:
            bought = buy_symbol(s['symbol'], trading_client, market_client, buying_power)

            if bought:
                sendAlpacaMessage("[Buy] %s with %s" % (s['symbol'], buying_power))

            account = trading_client.get_account()

            buying_power = float(account.buying_power)

def filter_strat(symbol, market_client, start):
    volume_threshold = float(os.getenv('VOLUME_THRESHOLD'))

    week_bars = get_bars(symbol, start - timedelta(days=7), start, market_client)

    if week_bars.empty:
        return False

    volume = week_bars['volume'].sum()
    return volume > volume_threshold

def trend_strat(symbols, market_client, start, notify, forceModel=False, debugInfo=False):
    buy = []
    sell = []

    for s in symbols:
        try:
            days = float(os.getenv('FULL_DAY_COUNT'))
            full_bars = get_bars(s, start - timedelta(days=days), start, market_client)

            if full_bars.empty:
                continue

            full_bars = feature_engineer_df(full_bars)

            current_stats = current_status(full_bars, debugInfo)
            current_trend = current_stats['cross']

            predicted_stats = predict_status(s, full_bars, forceModel, debugInfo)
            predicted_trend = predicted_stats['status']

            # Weigh based on predicted and current, give current a bit more so it buys sooner
            status = ''
            if current_trend == 'buy':
                status = 'buy'
                buy.append({ 'symbol': s, 'weight': 2 })
            elif current_trend == 'sell':
                status = 'sell'
                sell.append({ 'symbol': s, 'weight': 2 })
            elif predicted_trend == 'buy':
                status = 'buy'
                buy.append({ 'symbol': s, 'weight': 1 })
            elif predicted_trend == 'sell':
                status = 'sell'
                sell.append({ 'symbol': s, 'weight': 1 })

            if notify: #and current_trend != 'hold' or predicted_trend != 'hold':
                #TODO: Update to make this show what trend is being marked as buy/sell
                body = createMessageBody(current_stats, predicted_stats, full_bars)
                sendMessage(s, status, body)
        except Exception as e:
            print(e)

    def trendSort(k):
        return k['weight']

    buy.sort(key=trendSort)
    sell.sort(key=trendSort)

    return { 'buy': buy, 'sell': sell }

def createMessageBody(current_stats, predicted_stats, full_bars):
    crossover = "MA cross: %s" % current_stats['cross'].upper()
    predicted = "Predicted MA cross: %s" % predicted_stats['status'].upper()
    rsi = "RSI: %s" % current_stats['rsi'].upper()
    macd = "MACD: %s" % current_stats['macd'].upper()
    obv = "OBV: %s" % current_stats['obv'].upper()

    closing_message = "Bar: %s sold at $%s closed %s" % (full_bars.iloc[-1]['close'], "{:,}".format(full_bars.iloc[-1]['trade_count']), full_bars.iloc[-1].name[1].strftime("%X"))
    rsi_message = "RSI: %s" % round(full_bars.iloc[-1]['rsi'], 2)

    long_message = "MA Long Current: %s Predicted: %s" % (round(predicted_stats['predicted_long'],2), round(predicted_stats['predicted_short'],2))
    short_message = "MA Short Current: %s Predicted: %s" % (round(predicted_stats['predicted_short'],2), round(predicted_stats['predicted_long'],2))

    return "%s\n\n%s\n%s\n%s\n\n%s\n%s\n%s\n\n%s\n%s" % (closing_message, rsi_message, short_message, long_message, rsi, macd, obv, crossover, predicted)

def sendMessage(symbol, status, body):
    if status == 'buy':
        color = '087e20'
    elif status == 'sell':
        color = '7e2508'
    else:
        color = '41087e'
    stock_discord_url = os.getenv('STOCK_DISCORD_URL')
    discord = DiscordWebhook(stock_discord_url)
    embed = DiscordEmbed(title="%s" % symbol, description=body, color=color)
    discord.add_embed(embed)
    discord.execute()

def sendAlpacaMessage(message):
    alpaca_discord_url = os.getenv('ALPACA_DISCORD_URL')
    discord = DiscordWebhook(alpaca_discord_url, content=message)
    discord.execute()