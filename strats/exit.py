from helpers import get_data, options, tracker, features
from messaging import discord
from alpaca.common.exceptions import APIError

def exit(trading_client, option_client):
    positions = get_data.get_positions(trading_client)
    for p in positions:
        exit_position(p, trading_client, option_client)

'''
Three cases for an exit
1. The current cost of the contract(s) is below the defined risk level
2. We are above the defined reward level and a dip occurred - THIS MAY CHANGE A BIT
'''
def exit_position(position, trading_client, option_client):
    pl = float(position.unrealized_plpc)
    pl_amt = float(position.unrealized_pl)
    cost = float(position.cost_basis)
    market_value = float(position.market_value)
    contract = position.symbol

    risk = cost * .15
    stop_loss = cost - risk
    secure_gains = cost + (risk * 3)

    print(f'{contract} P/L % {pl} stop loss of {stop_loss} and secure gains of {secure_gains} current cost {market_value}')

    exit = False

    # If we have dropped below the stop loss amount we need to just sell it
    if market_value < stop_loss:
        exit = True
    elif pl > 0:
        # If we are above secure gains and recently had a pull back sell it
        hst = tracker.get(contract)
        if market_value > secure_gains:
            last_pl = hst.iloc[-1]['p/l']
            if pl < last_pl:
                exit = True
        else:
            close_slope = options.get_contract_slope(contract, -5, option_client)
            print(f'{contract} last 5 close slope is {close_slope}')
            # We are between 0 and secur gains, if we start trending down, it is probably worth selling
            if close_slope < -0.07:
                exit = True
            # We can check the pl and see if it dipped a lot 
            elif len(hst) > 1:
                # TODO: Maybe see about making this a percent barrier, rather than just sell if it dips
                last_pl = hst.iloc[-1]['p/l']
                if last_pl > 0:
                    diff = features.get_percentage_diff(last_pl, pl, True)
                    print(f'{contract} last p/l {last_pl} current p/l {pl} diff {diff}')
                    if diff < -30:
                        exit = True

    try:
        if exit:
            if pl_amt > 0:
                discord.send_alpaca_message(f'Selling {contract} at a profit of {pl_amt}')
            else:
                discord.send_alpaca_message(f'Selling {contract} at a loss of {pl_amt}')
            trading_client.close_position(contract)
            tracker.clear(contract)
        else:
            # If we don't sell we need to keep track
            tracker.track(contract, pl)
    except APIError as e:
        print(e)