from typing import List, Tuple
from src.helpers import options, tracker, features, get_data

import os
import math

class OptionExit:

    def __init__(self, trading_client) -> None:
        self.positions = []
        self.signals = []
        self.trading_client = trading_client

        self.slope_loss = int(os.getenv('SLOPE_LOSS'))
        self.stop_loss_val = int(os.getenv('STOP_LOSS'))
        self.slope_gains = int(os.getenv('SLOPE_GAINS'))
        self.secure_gains_val = int(os.getenv('SECURE_GAINS'))

    def add_positions(self, positions) -> None:
        self.positions = positions

    def load_positions(self, positions) -> None:
        self.positions = get_data.get_positions(self.trading_client)

    def add_signals(self, signals) -> None:
        self.signals = signals

    def exit(self) -> List[Tuple[dict, str]]:
        exits = []

        for position in self.positions:
            symbol = options.get_underlying_symbol(position.symbol)

            pl = float(position.unrealized_plpc) * 100
            cost = float(position.cost_basis)
            qty = float(position.qty)
            market_value = float(position.market_value)
            symbol_signal = next((s for s in self.signals if s['symbol'] == symbol), None)
            signal = 'Hold'
            if symbol_signal != None:
                signal = symbol_signal['signal']
            hst = tracker.get(position.symbol)

            slope = features.slope(hst['p/l'])[0] if len(hst) > 3 else 0
            immediate_slope = features.slope(hst[-3:]['p/l'])[0] if len(hst) > 3 else 0
            gains = (market_value - cost) / qty

            print(f'{position.symbol} P/L % {pl} gains {gains} current: {market_value} bought: {cost} signal: {signal} slope: {slope}/{immediate_slope}')

            if self.signal_check(signal, position, exits) or self.stop_loss(hst, pl, gains, position, market_value, slope, exits) or self.secure_gains(hst, gains, slope, position, exits):
                continue
         
            tracker.track(position.symbol, pl, gains, market_value)

        return exits
    
    def signal_check(self, signal, position, exits) -> bool:
        if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
            # Hold it we are signaling
            return True

        if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
            exits.append([position, 'reversal'])
            return True

        return False
    
    def secure_gains(self, hst, gains, slope, position, exits) -> bool:
        passed_secure_gains = not hst.empty and (hst['gains'] >= self.secure_gains_val).any()
        if passed_secure_gains and slope < 2:
            exits.append([position, 'secure gains'])
            return True
        
        if len(hst) > 5 and gains > self.slope_gains:
            if slope < -1:
                exits.append([position, 'secure gains with slope'])
                return True

        return False

    def stop_loss(self, hst, pl, gains, position, market_value, slope, exits) -> bool:
        if pl < 0:
            if -gains >= self.stop_loss_val:
                exits.append([position, 'stop loss'])
                return True

            if len(hst) > 5 and -gains < self.slope_loss:
                if slope < -1:
                    exits.append([position, 'stop loss with slope'])
                    return True

        return False