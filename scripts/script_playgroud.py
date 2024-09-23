import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from src.helpers import options

def run(type, strike_price, dte):
    up_close = 100
    down_close = 100
    for b in range(60):
        dte = dte - 0.03
        up_contract_price = options.get_option_price(type, up_close, strike_price, dte, 0.05, .1181)
        down_contract_price = options.get_option_price(type, down_close, strike_price, dte, 0.05, .1181)
        print(f'{type} -> Up {up_contract_price}/{up_close} Down {down_contract_price}/{down_close}')
        up_close = up_close + .1
        down_close = down_close - .1

run('call', 100, 2)
run('put', 97, 2)
