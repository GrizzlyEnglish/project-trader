import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from polygon import RESTClient
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.data import options_data, bars_data
from src.helpers import options, features
from src.strategies import short_option

import numpy as np
import pandas as pd

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")
polygon_key = os.getenv("POLYGON_KEY")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)
polygon_client = RESTClient(api_key=polygon_key)

symbol = 'QQQ'

end = datetime(2024, 12, 6, 19)
start = end - timedelta(days=90)

bars_handlers = bars_data.BarData(symbol, start - timedelta(days=30), end, market_client)
bars = bars_handlers.get_bars(1, 'Min')

strat = short_option.ShortOption()
bars = strat.enter(bars)


pd.DataFrame(data=bars).to_csv(f'../results/signals.csv', index=True)