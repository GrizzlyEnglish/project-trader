import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from polygon import RESTClient
from dotenv import load_dotenv
from datetime import datetime, timedelta

from src.backtesting import options_short
from src.helpers import chart

import ast
import time
import numpy as np
import matplotlib.pyplot as plt

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
day_diff = int(os.getenv('DAYDIFF'))
symbols = ast.literal_eval(os.getenv('SYMBOLS'))
polygon_key = os.getenv("POLYGON_KEY")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

end = datetime(2024, 12, 9, 12, 30)
runner = options_short.BacktestOptionShort(symbols, end, 90, day_diff, market_client, trading_client, option_client)
t = runner.run(False)

#chart.chart(np.array(runner.account_bars), 'Account value', 'Bar index', '$', 1)

plt.show()