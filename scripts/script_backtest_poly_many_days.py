import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from polygon import RESTClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import chart

from src.backtesting import options_short

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

totals = []
account_bars = []
end = datetime(2024, 12, 2, 12, 30)
diff = 5
for i in range(10):
    runner = options_short.BacktestOptionShort(symbols, end, diff, day_diff, market_client, trading_client, option_client, polygon_client)
    t = runner.run(False)
    totals.append([end, t])
    end = end - timedelta(days=diff)
    for ab in runner.account_bars:
        account_bars.append([len(account_bars) + 1, ab[1]])
    time.sleep(75)

for t in totals:
    print(f'{t[0]}={t[1]}')

chart.chart(np.array(account_bars), 'Account value', '$', 'Bar index', 1)

plt.show()