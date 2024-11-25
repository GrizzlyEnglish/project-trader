import os,sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))

from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from dotenv import load_dotenv
from datetime import datetime, timedelta
from src.helpers import get_data, features

import os
import numpy as np
from scipy.optimize import newton

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

trading_client = TradingClient(api_key, api_secret, paper=paper)
market_client = StockHistoricalDataClient(api_key, api_secret)
option_client = OptionHistoricalDataClient(api_key, api_secret)

end = datetime(2024, 11, 19)
df = get_data.get_bars('QQQ', end - timedelta(days=30), end, market_client)
df = features.feature_engineer_df(df)
row_df1 = df.iloc[-1]

df2 = get_data.get_bars('QQQ', end - timedelta(days=90), end, market_client)
df2 = features.feature_engineer_df(df2)
row_df2 = df2.iloc[-1]

differences = row_df1 != row_df2
print(differences[differences].index.tolist())

print(row_df1['upper_KC__last__last__last'])
print(row_df2['upper_KC__last__last__last'])
print(row_df1['lower_KC__last__last__last'])
print(row_df2['lower_KC__last__last__last'])