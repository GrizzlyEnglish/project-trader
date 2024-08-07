from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.enums import AssetClass
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

enters = scalp.enter(assets, market_client, datetime.now())

for enter in enters:
    contracts = []
    if enter['type'] == 'call':
        contracts = options.get_option_call_itm(enter['symbol'], enter['price'], trading_client).option_contracts
    else:
        contracts = options.get_option_putt_itm(enter['symbol'], enter['price'], trading_client).option_contracts
    contract = contracts[1]
    buying_power = get_data.get_buying_power(trading_client)
    qty = options.get_option_buying_power(contract, buying_power, enter['type'] == 'put')['qty']
    buy.submit_order(contract.symbol, qty, trading_client)

current_positions = trading_client.get_all_positions()
positions = [p for p in current_positions if p.asset_class == AssetClass.US_OPTION]
exits = scalp.exit(enters, positions)

for exit in exits:
    trading_client.close_position(exit)