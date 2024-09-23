from src.helpers import get_data, tracker, features, options
from src.messaging import discord
from alpaca.common.exceptions import APIError

stop_loss_reason = 'stop loss'
slope_loss_reason = 'over gains and trending down'
perc_diff_loss_reason = 'over gains and big drop' 

def exit(trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    for p in positions:
        exit_position(p, trading_client, option_client)

def exit_position(position, trading_client, option_client):
    pl = float(position.unrealized_plpc)
    pl_amt = float(position.unrealized_pl)
    cost = float(position.cost_basis)
    market_value = float(position.market_value)
    contract = position.symbol

    stop_loss, secure_gains = options.determine_risk_reward(cost)

    print(f'{contract} P/L % {pl} stop loss of {stop_loss} and secure gains of {secure_gains} current cost {market_value}')

    hst = tracker.get(contract)
    exit, reason = check_for_exit(hst, market_value, stop_loss, secure_gains)

    try:
        if exit:
            type = 'at a loss'
            if pl_amt > 0:
                type = 'for a profit'

            discord.send_alpaca_message(f'Selling {contract} {type} {pl_amt} because of {reason}')
            trading_client.close_position(contract)
            tracker.clear(contract)
        else:
            # If we don't sell we need to keep track
            tracker.track(contract, pl)
    except APIError as e:
        print(e)

'''
Reasons for exiting
1. Dropped below our risk tolerance
2. Above our secure gains, and enough of a drop to just leave
'''
def check_for_exit(hst, market_value, stop_loss, secure_gains):
    reason = ''
    exit = False

    # Check if we are below our risk allowance, exit if below
    exit, reason = check_risk_tolerance(market_value, stop_loss)

    # Check if we are above our secure gains, and we dipped, exit
    exit, reason = check_reward_tolerance(hst, market_value, secure_gains)

    return exit, reason

def check_risk_tolerance(market_value, stop_loss):
    return market_value < stop_loss, stop_loss_reason 

def check_reward_tolerance(hst, market_value, secure_gains):
    if market_value >= secure_gains and len(hst) > 1:
        last_market_value = hst.iloc[-1]['market_value']
        if len(hst) > 4:
            last_slope = round(features.slope(hst.iloc[-2:]['market_value'])[0], 3)
            last_two_slope = round(features.slope(hst.iloc[-4:-2]['market_value'])[0], 3)
            if last_slope < last_two_slope:
                return True, slope_loss_reason
        perc_diff = features.get_percentage_diff(last_market_value, market_value, False)
        if perc_diff < -3:
            return True, perc_diff_loss_reason
    
    return False, ''