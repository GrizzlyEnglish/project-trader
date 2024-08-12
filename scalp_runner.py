from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import AssetClass
from alpaca.common.exceptions import APIError
from dotenv import load_dotenv
from helpers.load_stocks import load_symbols
from helpers import options, get_data, buy
from datetime import datetime, timedelta
from strats import scalp

import os

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)

assets = load_symbols('scalp_symbols.txt')

while (True):
    enters = scalp.enter(assets, market_client, datetime.now())

    current_positions = trading_client.get_all_positions()

    for enter in enters:
        contracts = []
        if enter['type'] == 'call':
            contracts = options.get_option_call_itm(enter['symbol'], enter['price'], trading_client)[-3:]
        else:
            contracts = options.get_option_put_itm(enter['symbol'], enter['price'], trading_client)[:3]
        
        for contract in contracts:
            owned = next((cp for cp in current_positions if enter['symbol'] in cp.symbol), None)

            if owned == None:
                buying_power = get_data.get_buying_power(trading_client)
                qty = options.get_option_buying_power(contract, buying_power, enter['type'] == 'put')['qty']
                if qty != None and qty > 0:
                    buy.submit_order(contract.symbol, qty, trading_client, False)

    positions = [p for p in current_positions if p.asset_class == AssetClass.US_OPTION]
    exits = scalp.exit(positions, assets, datetime.now(), market_client)

    for exit in exits:
        try:
            trading_client.close_position(exit)
        except APIError as e:
            print(e)