from typing import Tuple
from datetime import datetime, time, timezone

from src.helpers import options, tracker, features

import os
import pandas as pd

class LongOption:

    def __init():
        pass

    def exit(self, position, bar) -> Tuple[dict, str]:
        symbol = options.get_underlying_symbol(position.symbol)

        stop_loss_val = int(os.getenv(f'{symbol}_STOP_LOSS'))
        pvi_gain_gaurd = float(os.getenv(f'{symbol}_GAIN_GAURD'))

        pl = float(position.unrealized_plpc) * 100
        cost = float(position.cost_basis)
        qty = float(position.qty)
        market_value = float(position.market_value)
        hst = tracker.get(position.symbol)

        gains = (market_value - cost) / qty

        print(f'{position.symbol} P/L % {pl} gains {gains} current: {market_value} bought: {cost} nvi {bar["nvi_short_trend"]}/{bar["nvi_long_trend"]} pvi {bar["pvi_short_trend"]}/{bar["pvi_long_trend"]}')

        tracker.track(position.symbol, pl, gains, market_value)

        loss_exit, reason = self.stop_loss(pl, gains, stop_loss_val)
        if loss_exit:
            return True, reason

        gains_exit, reason = self.secure_gains(bar, pvi_gain_gaurd, gains)
        if gains_exit:
            return True, reason
        
        return False, 'hold'
    
    def buy_amt(self) -> int:
        #TODO: Add logic? like based on account?
        return 1
    
    def signal_check(self, signal, position) -> bool:
        if (signal == 'Buy' and position.symbol[-9] == 'C') or (signal == 'Sell' and position.symbol[-9] == 'P'):
            # Hold it we are signaling
            return False, 'hold'

        if (signal == 'Buy' and position.symbol[-9] == 'P') or (signal == 'Sell' and position.symbol[-9] == 'C'):
            return True, 'reversal'

        return False, 'hold'
    
    def secure_gains(self, bar, pvi_gain_gaurd, gains) -> bool:
        if gains > 0 and bar['pvi'] < bar['pvi__last'] and bar['pvi_short_trend'] < -pvi_gain_gaurd and bar['close_short_trend'] < 0:
            return True, 'secure gains'
        
        return False, 'hold'

    def stop_loss(self, pl, gains, stop_loss_val) -> bool:
        if pl < 0:
            g = -gains
            if g >= stop_loss_val:
                return True, 'stop loss'

        return False, 'hold'

    def enter(self, bars) -> pd.DataFrame:
        def determine_signal(row): 
            idx = row.name[1]
            market_open = datetime.combine(idx, time(13, 30), timezone.utc)
            market_close = datetime.combine(idx, time(19, 1), timezone.utc)

            if idx <= market_open or idx >= market_close:
                return 'hold'

            if row['long_indicator'] == 1:
                return 'buy'
            elif row['long_indicator'] == -1:
                return 'sell'
            else:
                return 'hold'
            
        b = bars.copy()
        #b['long_indicator'] = b.apply(features.long_indicator, axis=1)
        b['long_indicator'] = b.apply(features.vortext_indicator_long, axis=1)
        b['signal'] = b.apply(determine_signal, axis=1)

        return b
