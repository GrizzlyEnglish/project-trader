from src.helpers import get_data, tracker, features, options
from src.messaging import discord
from alpaca.common.exceptions import APIError

def exit(position, reason, trading_client):
    pl = float(position.unrealized_plpc)
    pl_amt = float(position.unrealized_pl)
    cost = float(position.cost_basis)
    contract = position.symbol

    try:
        type = 'at a loss'
        if pl_amt > 0:
            type = 'for a profit'

        discord.send_alpaca_message(f'Selling {contract} {type} {pl_amt} because of {reason}')
        trading_client.close_position(contract)
        tracker.clear(contract)
    except APIError as e:
        print(e)