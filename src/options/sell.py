from alpaca.common.exceptions import APIError
from src.messaging import discord
from src.helpers import tracker

class Sell:

    def __init__(self, trading_client, option_client) -> None:
        self.trading_client = trading_client
        self.option_client = option_client

    def exit(self, position, reason) -> None:
        pl = float(position.unrealized_plpc)
        pl_amt = float(position.unrealized_pl)
        cost = float(position.cost_basis)
        contract = position.symbol

        try:
            type = 'at a loss'
            if pl_amt > 0:
                type = 'for a profit'

            discord.send_alpaca_message(f'Selling {contract} {type} {pl_amt} because of {reason}')
            self.trading_client.close_position(contract)
            tracker.clear(contract)
        except APIError as e:
            print(e)