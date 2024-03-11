from stocks.penny_stock_strat import penny_stock_strat
from datetime import datetime, timedelta

import time

#TODO: Move to env vars?
api_key = ''
api_secret = ''

#stocks = ['FSR', 'NKLA', 'BKKT', 'OPK', 'CLOV', 'AGEN', 'GOEV', 'GEVO', 'SENS', 'KSCP', 'ORGN', 'WKHS', 'PXDT', 'LILM', 'DOYU', 'LFWD', 'HOOK']
stocks = ['HOOK']
sleep_time = 60

window_in_min = 15
rolling_small_window = 3
rolling_large_window = 8

window_start = datetime(2024, 3, 8, 18, 0)
window_end = window_start + timedelta(minutes=100)

# TODO: Actually run some back tests, not just call it in the past
penny_stock_strat(stocks, window_start, window_end, 12, api_key, api_secret, True)

print("Sleeping for %s" % str(sleep_time))
time.sleep(sleep_time)