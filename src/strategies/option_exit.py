from typing import List, Tuple
from src.helpers import options, tracker, features, get_data

import os
import math

class OptionExit:

    def __init__(self, trading_client) -> None:
        self.positions = []
        self.signals = []
        self.trading_client = trading_client

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

            if symbol == 'SPY' or symbol == 'QQQ':
                risk = int(os.getenv('HIGH_RISK'))
                reward_scale = int(os.getenv(f'HIGH_RISK_SCALE'))
            else:
                risk = int(os.getenv('LOW_RISK'))
                reward_scale = int(os.getenv(f'LOW_RISK_SCALE'))

            pl = float(position.unrealized_plpc) * 100
            cost = float(position.cost_basis)
            qty = float(position.qty)
            market_value = float(position.market_value)
            symbol_signal = next((s for s in self.signals if s['symbol'] == symbol), None)
            signal = 'Hold'
            if symbol_signal != None:
                signal = symbol_signal['signal']
            hst = tracker.get(position.symbol)

            # Determine the actual amount we are risking, and how much to gain
            risk = min(cost, risk*qty)
            reward = risk * reward_scale

            secure_gains = math.floor(cost + reward)
            stop_loss = math.floor(cost - risk)

            slope = features.slope(hst['p/l'])[0] if len(hst) > 3 else 0

            print(f'{position.symbol} P/L % {pl} {stop_loss}/{secure_gains} current: {market_value} bought: {cost} signal: {signal} slope: {slope}')

            if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
                # Hold it we are signaling
                continue

            if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
                exits.append([position, 'reversal'])
                continue
            
            passed_secure_gains = not hst.empty and (hst['market_value'] >= secure_gains).any()
            if passed_secure_gains:
                if market_value <= (secure_gains + 1):
                    exits.append([position, 'secure_gains'])
                    continue

                idx = hst.index[hst['market_value'] >= secure_gains][0]
                sub_hst = hst.iloc[idx:]['market_value']
                if len(sub_hst) > 3:
                    slope = features.slope(sub_hst)[0]
                    if slope < 1:
                        exits.append([position, 'secure_gains'])
                        continue
                    
            if pl < 0 and len(hst) > 5 and stop_loss > 75:
                if slope < -5:
                    exits.append([position, 'stop loss with slope'])
                    continue

            if market_value <= stop_loss:
                exits.append([position, 'stop loss'])
                continue     
         
            tracker.track(position.symbol, pl, market_value)

        return exits