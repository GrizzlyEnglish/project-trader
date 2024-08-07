from alpaca.trading.requests import GetOptionContractsRequest
from alpaca.trading.enums import AssetStatus
from datetime import timedelta, datetime
from matplotlib import pyplot as plt
from helpers import get_data
from PIL import Image

import pandas
import matplotlib.pyplot as plt
import numpy as np

def create_sentiment_file(symbol, trading_client, market_client):
    now = datetime.now()
    until = now + timedelta(days=14)

    now_str = now.strftime(format="%Y-%m-%d")
    until_str = until.strftime(format="%Y-%m-%d")

    bars = get_data.get_bars(symbol, datetime.now() - timedelta(days=1), datetime.now(), market_client)

    if bars.empty:
        return ''
    
    close = bars['close'].iloc[-1]

    top = (close + (close * .15))
    bottom = (close - (close * .15))
    print(top)
    print(bottom)
    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now_str,  
        expiration_date_lte=until_str,  
        root_symbol=symbol,                                    
        strike_price_gte=str(bottom),
        strike_price_lte=str(top),
        type="call"
    )

    options = trading_client.get_option_contracts(req)
    call_contracts = options.option_contracts

    req = GetOptionContractsRequest(
        underlying_symbol=[symbol],                 
        status=AssetStatus.ACTIVE,                           
        expiration_date_gte=now_str,  
        expiration_date_lte=until_str,  
        root_symbol=symbol,                                    
        strike_price_gte=str(bottom),                               
        strike_price_lte=str(top),                               
        type="put"
    )

    options = trading_client.get_option_contracts(req)
    put_contracts = options.option_contracts

    contracts = call_contracts + put_contracts

    strike_prices = [c.strike_price for c in contracts]
    strike_prices.sort()
    print(len(strike_prices))

    strikes = []
    calls = []
    puts = []

    for strike in strike_prices:
        if strike in strikes:
            continue

        call = next((c for c in contracts if c.type == "call" and c.strike_price == strike), None)
        put = next((c for c in contracts if c.type == "put" and c.strike_price == strike), None)

        if call == None and put == None:
            continue

        strikes.append(strike)

        if not call == None and not call.open_interest == None:
            calls.append(float(call.open_interest))
        else:
            calls.append(0)

        if not put == None and not put.open_interest == None:
            puts.append(float(put.open_interest))
        else:
            puts.append(0)

    df = pandas.DataFrame(dict(graph=strikes, n=calls, m=puts)) 

    ind = np.arange(len(df))
    width = 0.3

    fig, ax = plt.subplots()
    fig.subplots_adjust(
        top=0.981,
        bottom=0.049,
        left=0.042,
        right=0.981,
        hspace=0.2,
        wspace=0.2
    )
    fig.set_size_inches(18.5, 20.5)
    ax.barh(ind, df.n, width, color='green', label='Calls')
    ax.barh(ind + width, df.m, width, color='red', label='Puts')

    ax.set(yticks=ind + width, yticklabels=df.graph, ylim=[4*width - 1, len(df)])
    ax.set_title("%s Contracts until %s" % (symbol, until_str), fontdict={'fontsize': 16, 'fontweight': 'medium'})
    ax.legend()

    fileName = symbol + '.png'
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=10)
    plt.savefig(fileName)

    image = Image.open(fileName)
    image.save(fileName,quality=20,optimize=True)
    
    return fileName