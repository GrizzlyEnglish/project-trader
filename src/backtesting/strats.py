from src.helpers import options, tracker
from src.strats import enter, exit

def check_for_entry(signal, close_price, call_var, put_var, index, strike_price, symbol, look_forward, dte, r, vol):
    if signal['signal'] == 'Hold':
        return

    contract_type = 'put'
    expected_var = put_var

    if signal['signal'] == 'Buy':
        contract_type = 'call'
        expected_var = call_var

    contract_price = options.get_option_price(contract_type, close_price, strike_price, dte, r, vol)
    if enter.check_contract_entry(index, contract_type, strike_price, contract_price, contract_price, vol, r, dte, close_price, expected_var, look_forward):
        print(f'Purchased {contract_type} at {contract_price} with underlying at {close_price} with r {r} and vol {vol}')
        mv = contract_price*100
        stop_loss, secure_gains = options.determine_risk_reward(mv)
        return {
            'strike_price': strike_price,
            'close': close_price,
            'type': contract_type,
            'price': contract_price,
            'dte': dte,
            'stop_loss': stop_loss,
            'market_value': mv,
            'secure_gains': secure_gains,
            'bought_at': index
        }

    return None

def check_for_exit(symbol, close_price, index, open_contract, signal, r, vol):
    hst = tracker.get(symbol)
    contract_price = options.get_option_price(open_contract['type'], close_price, open_contract['strike_price'], open_contract['dte'], r, vol)
    mv = contract_price*100
    exit_contract, reason = exit.check_for_exit(hst, open_contract['type'], signal, mv, open_contract['stop_loss'], open_contract['secure_gains'])

    if exit_contract:
        print(f'Sold {symbol} {open_contract["type"]} for profit of {contract_price - open_contract["price"]} underlying {close_price - open_contract["close"]} held for {len(hst)}')
        tracker.clear(symbol)
        return True, mv, reason

    tracker.track(symbol, 0, mv)
    return False, mv, ''