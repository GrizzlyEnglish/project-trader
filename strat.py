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

import numpy as np
import os

MAX_WEIGHT = 20

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

def sell_strat(symbol_trends, trading_client):
    current_positions = trading_client.get_all_positions()

    stop_loss = float(os.getenv('STOP_LOSS'))

    for p in current_positions:
        pl = float(p.unrealized_plpc)

        trend = next((s for s in symbol_trends if s['symbol'].replace("/", "") == p.symbol), None)

        sell = False

        weight = 0

        if trend != None:
            weight = trend['weight']

        if pl > 0:
            # Profit if we have any chance of loss sell, if low chance of gain sell
            sell = weight < 4
        elif pl < -stop_loss:
            # Very low, unless high chance of gain sell it
            sell = weight > 6
        else:
            # We are loosing if there is huge chance of gain we can
            sell = weight < 2

        if sell:
            try:
                previous_date = datetime.now() - timedelta(hours=12)
                orders = trading_client.get_orders(GetOrdersRequest(status='closed', after=previous_date, side=OrderSide.BUY, symbols=[p.symbol])) 
                if len(orders) == 0:
                    sell_symbol(p, trading_client)
                    sendAlpacaMessage("[Sell] Sold %s with p/l of %s and a weight of %s" % (p.symbol, pl, weight))
            except Exception as e:
                print(e)
                sendAlpacaMessage("[Sell] Failed to sell %s 'cause %s" % (p.symbol, e))
        else:
            sendAlpacaMessage("[Sell] Did not sell %s with p/l of %s and a weight of %s" % (p.symbol, pl, weight))

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
    trends = []

    for s in symbols:
        try:
            days = float(os.getenv('FULL_DAY_COUNT'))
            full_bars = get_bars(s, start - timedelta(days=days), start, market_client)

            if full_bars.empty:
                continue

            full_bars = feature_engineer_df(full_bars)

            current_stats = current_status(full_bars, debugInfo)

            predicted_stats = predict_status(s, full_bars, forceModel, debugInfo)

            weight = get_weight(current_stats, predicted_stats)

            trends.append({ 'symbol': s, 'weight': weight })

            if notify: #and current_trend != 'hold' or predicted_trend != 'hold':
                #TODO: Update to make this show what trend is being marked as buy/sell
                body = createMessageBody(current_stats, predicted_stats, full_bars, weight)
                sendMessage(s, weight, body)
        except Exception as e:
            print(e)

    def trendSort(k):
        return k['weight']

    trends.sort(key=trendSort)

    return trends

# MAX = 20
# MIN = -20
def get_buy_sell_weight(status, scale):
    if status == "buy":
        return scale
    elif status == "sell":
        return scale * -1
    return 0

def get_weight(current_stats, predicted_stats):
    # Weigh the buy/sell in order to make better purchases
    weight = 0
    # Current trends weigh higher and RSI>MACD>OBV
    weight += get_buy_sell_weight(current_stats['rsi'], 6)
    weight += get_buy_sell_weight(current_stats['macd'], 5)
    weight += get_buy_sell_weight(current_stats['obv'], 4)

    # Predicted weighs less and CROSS>PRICE
    weight += get_buy_sell_weight(predicted_stats['predicted_cross'], 3)
    weight += get_buy_sell_weight(predicted_stats['predicted_price'], 2)

    return weight

def createMessageBody(current_stats, predicted_stats, full_bars, weight):
    up_arrow = "\u2191"
    down_arrow = "\u2193"
    side_bar = "\u2015"

    # Bar info
    trade_count = "{:,}".format(full_bars.iloc[-1]['trade_count'])
    last_close = full_bars.iloc[-1]['close']
    last_close_time = full_bars.iloc[-1].name[1].strftime("%X")
    closing_message = "%s sold at $%s closed %s" % (trade_count, last_close, last_close_time)

    avg_future = predicted_stats['future_close']
    future_arrow = side_bar
    if avg_future < last_close:
        future_arrow = down_arrow
    elif avg_future > last_close:
        future_arrow = up_arrow
    predicted_closing_message = "%s Predicted: $%s closing in +24hr" % (future_arrow, avg_future)

    #MA Info
    current_crossover = "Current: %s" % current_stats['cross'].upper()
    predicted_crossover = "Predicted: %s" % predicted_stats['predicted_cross'].upper()

    #Trend Info
    rsi_message = "RSI: %s | %s" % (round(full_bars.iloc[-1]['rsi'], 2), current_stats['rsi'].upper())
    macd = "MACD: %s" % current_stats['macd'].upper()
    obv = "OBV: %s" % current_stats['obv'].upper()
    weight_message = "WEIGHT: %s" % weight

    return "Bar\n%s\n%s\n\nMA\n%s\n%s\n\nTrend\n%s\n%s\n%s\n\nBot Info\n%s" % (closing_message, predicted_closing_message, current_crossover, predicted_crossover, rsi_message, macd, obv, weight_message)

def sendMessage(symbol, weight, body):
    if weight > 0:
        color = '087e20'
    elif weight < 0:
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
    discord = DiscordWebhook(alpaca_discord_url, content=message, rate_limit_retry=True)
    discord.execute()