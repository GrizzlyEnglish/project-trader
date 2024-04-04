import pandas as pd

from helpers.buy import buy_stocks
from helpers.sell import sell_stocks
from helpers.trend_logic import predict_ewm_12

def crypto_strat(coins, trading_client, crypto_market_client):

    # Check if we have any current coins that we should sell
    current_positions = trading_client.get_all_positions()
    sell = []

    for p in current_positions:
        print("Current position on %s %s with a p/l of %s" % (p.symbol, p.qty, p.unrealized_pl))

        predicted = predict_ewm_12(p.symbol, crypto_market_client)

        pl = float(p.unrealized_pl)
        current_price = float(p.current_price)

        # If loss and trending down OR
        if (pl < 0 and predicted['difference'] < -3) or (pl > 0 and predicted['difference'] < 0 and predicted['price'] < current_price):
            print("Setting % s to sell at unrealized pl of %s and a predicted ewm of %s with a difference of %s" % (p.symbol, p.unrealized_pl, predicted['price'], predicted['difference']))
            sell.append(p.symbol)

        sell_stocks(sell, trading_client)

    # Check if we have buying power and go through and see if there are any coins worth purchasing
    buy = []

    account = trading_client.get_account()

    buying_power = float(account.buying_power)

    if buying_power > 0:
        for coin in coins:
            # reset buying power
            account = trading_client.get_account()

            buying_power = float(account.buying_power)

            predicted = predict_ewm_12(coin, crypto_market_client)

            if predicted['difference'] > 0:
                print("Setting % s to buy with a predicted difference of %s" % (coin, predicted['difference']))
                buy.append(coin)

        buy_stocks(buy, trading_client, crypto_market_client, buying_power)