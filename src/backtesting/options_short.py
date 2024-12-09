from datetime import datetime, time, timezone, timedelta
from src.strategies import short_option 
from src.helpers import options, features, tracker
from src.data import options_data, bars_data

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz

class BacktestOptionShort:

    def __init__(self, symbols, end, days, day_diff, market_client, trading_client, option_client, polygon_client, use_polygon = False) -> None:
        self.symbols = symbols
        self.end = end
        self.start = end - timedelta(days=days)
        self.market_client = market_client
        self.trading_client = trading_client
        self.option_client = option_client
        self.polygon_client = polygon_client
        self.day_diff = day_diff
        self.close_series = {}
        self.purchased_series = {}
        self.sell_series = {}
        self.pl_series = []
        self.telemetry = []
        self.positions = []
        self.actions = 0
        self.correct_actions = 0
        self.total = {}
        self.use_polygon = use_polygon

        self.account = 30000
        self.account_bars = []

        self.held_option_bars = {}

        for s in self.symbols:
            self.close_series[s] = []
            self.purchased_series[s] = []
            self.sell_series[s] = []
            self.total[s] = 0

    def enter(self, symbol, row, signal, buy_qty) -> None:
        index = row.name[1]

        # TODO: Move to strat
        market_open = datetime.combine(index, time(13, 30), timezone.utc)
        market_close = datetime.combine(index, time(19, 1), timezone.utc)

        if index <= market_open or index >= market_close:
            print('Not purcharsing outside market hours')
            return None, None

        close = row['close']
        type = 'P'
        contract_type = 'put'
        if signal == 'buy':
            type = 'C'
            contract_type = 'call'

        data = options_data.OptionData(symbol, index, type, close, self.option_client, self.polygon_client)
        data.set_polygon(self.use_polygon)

        bars = data.get_bars(index.replace(hour=9), index.replace(hour=23))

        if bars.empty:
            print(f'No bars for {data.symbol}')
            return None, None

        up_to = bars[bars.index.get_level_values('timestamp') <= index]
        contract_price = up_to['close'].iloc[-1] * buy_qty

        bars = bars[bars.index.get_level_values('timestamp') >= index]

        if contract_price > 0:
            class DotAccessibleDict:
                def __init__(self, **entries):
                    self.__dict__.update(entries)
            position = DotAccessibleDict(**{
                'symbol': data.symbol,
                'contract_type': contract_type,
                'strike_price': data.strike,
                'close': close,
                'price': contract_price,
                'cost_basis': contract_price * 100,
                'bought_at': index,
                'qty': buy_qty,
                'market_value': contract_price * 100,
                'unrealized_plpc': 0,
                'date_of': index.date()
            })
            print(f'Purchased {data.symbol} at {index} with close at {close}')
            self.purchased_series[symbol].append(index)
            self.account = self.account - (contract_price * 100)
            return position, bars
        
        return None, None

    def exit(self, p, symbol, reason, index) -> None:
        print(f'Sold {p.symbol} for {reason}')
        tel = {
            'contract': p.symbol,
            'strike_price': p.strike_price,
            'type': p.contract_type,
            'bought_price': p.cost_basis,
            'sold_price': float(p.market_value),
            'bought_at': p.bought_at,
            'sold_at': index,
            'held_for': index - p.bought_at,
            'sold_for': reason,
            'pl': (float(p.market_value) - p.cost_basis),
            'qty': p.qty
        }
        self.sell_series[symbol].append(index)
        self.telemetry.append(tel)
        pl = tel['sold_price'] - tel['bought_price']
        self.pl_series.append([tel['type'], pl])
        self.actions = self.actions + 1
        if pl > 0:
            self.correct_actions = self.correct_actions + 1
        self.total[symbol] = self.total[symbol] + (float(p.market_value) - p.cost_basis)
        tracker.clear(p.symbol)
        self.account = self.account + float(p.market_value)

    def run(self, show_graph = True) -> int:
        start_dt = self.start
        end_dt = self.end

        start_dt = start_dt.replace(hour=23, minute=59, second=0, microsecond=0) 
        start_dt = pytz.UTC.localize(start_dt)

        print(f'Back test from {start_dt} to {end_dt}')

        strat = short_option.ShortOption()

        for symbol in self.symbols:
            # Get all the bars in this time frame and look for my indicators
            bars_handlers = bars_data.BarData(symbol, start_dt - timedelta(days=30), end_dt, self.market_client)
            bars = bars_handlers.get_bars(1, 'Min')

            # Only do what we want
            bars = bars[bars.index.get_level_values('timestamp') >= start_dt]

            # Get just the ones we'd buy
            bars = strat.enter(bars)

            # Need to know when we were holding so if a signal happens when holding we dont buy extra
            held_positions = []

            # Enter and find exit
            for index, row in bars.iterrows():
                print(f'Signal for {symbol} on {index[1]}')

                # Check if holding
                currently_holding = False
                for hp in held_positions:
                    if index[1] >= hp[0] and index[1] <= hp[1]:
                        print('Holding a position dont enter this')
                        currently_holding = True
                        break

                if currently_holding:
                    continue

                # Enter
                #TODO: determine how to increase buy amount
                position, position_bars = self.enter(symbol, row, row['signal'], 1)

                # Determine exit
                if position != None:
                    entered = index[1]
                    reason = 'expired'
                    for pindex, prow in position_bars.iterrows():
                        print(f'Checking {position.symbol} at {pindex}')

                        mv = prow['close'] * 100

                        qty = float(position.qty)
                        mv = mv * qty
                        pld = features.get_percentage_diff(position.cost_basis, mv) / 100

                        position.unrealized_plpc = f'{pld}'
                        position.market_value = f'{mv}'

                        exit, reason = strat.exit(position, prow)
                        if exit:
                            break

                    self.exit(position, symbol, reason, pindex[1])
                    held_positions.append([entered, pindex[1]])

        full_total = 0
        for cs in self.symbols:
            full_total = full_total + self.total[cs]
            print(f'{cs} total {self.total[cs]}')

        accuracy = 0
        if self.actions > 0:
            accuracy = self.correct_actions/self.actions
            print(f'Accuracy {accuracy} total {full_total}')
        
        if len(self.positions) > 0:
            for p in self.positions:
                print(f'Still holding {p.symbol} with pl {p.unrealized_plpc}')

        pd.DataFrame(data=self.telemetry).to_csv(f'../results/short_backtest_{self.start.strftime("%Y_%m_%d")}_{self.end.strftime("%Y_%m_%d")}.csv', index=True)

        if show_graph:
            fig = plt.figure(1)

            pl_series = np.array(self.pl_series)
            x = [float(p) for p in pl_series[:, 1]]
            y = pl_series[:, 0]
            categories = [f'{y[i]} {i+1}' for i in range(len(y))]

            plt.bar(categories, x, color=['orange' if 'call' in value else 'purple' for value in y])

            plt.xlabel('Option type')
            plt.ylabel('P/L')
            plt.title('Option backtest p/l')

            # Show the plot
            plt.show()
        
        return full_total