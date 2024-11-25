import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import options_short

import ast

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
day_diff = int(os.getenv('DAYDIFF'))
symbols = ast.literal_eval(os.getenv('SYMBOLS'))
buy_amount = int(os.getenv('BUY_AMOUNT'))

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

end = datetime(2024, 11, 21, 12, 30)
start = end - timedelta(days=1)

runner = options_short.BacktestOptionShort(symbols, end, 1, buy_amount, day_diff, market_client, trading_client, option_client)
runner.run()
