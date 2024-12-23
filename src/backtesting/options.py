from datetime import datetime, time, timezone, timedelta
from src.strategies import short_option, long_option
from src.helpers import options, features, tracker
from src.data import options_data, bars_data

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pytz
import math

class BacktestOption:

    def __init__(self, shorts, longs, end, days, day_diff, market_client, trading_client, option_client) -> None:
        self.shorts = shorts
        self.longs = longs
        self.symbols = shorts + longs
        self.end = end
        self.start = end - timedelta(days=days)
        self.market_client = market_client
        self.trading_client = trading_client
        self.option_client = option_client
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

        self.account = 30000
        self.account_bars = {}
        self.returns = {}

        self.correct_bars = {}
        self.incorrect_bars = {}

        self.missing_bars = []

        for s in self.symbols:
            self.account_bars[s] = []
            self.close_series[s] = []
            self.purchased_series[s] = []
            self.sell_series[s] = []
            self.total[s] = 0
            self.correct_bars[s] = []
            self.incorrect_bars[s] = []
            self.returns[s] = []

    def enter(self, symbol, row, signal, buy_qty) -> None:
        index = row.name[1]

        close = row['close']
        type = 'P'
        contract_type = 'put'
        if signal == 'buy':
            type = 'C'
            contract_type = 'call'

        data = options_data.OptionData(symbol, index, type, close, self.option_client)
        bars = data.get_bars((index - timedelta(days=1)).replace(hour=9), index + timedelta(days=1))

        if bars.empty:
            print(f'No bars for {data.symbol}')
            self.missing_bars.append(data.symbol)
            return None, None, 0

        # Make sure we are only looking at the bars for the given date
        bars = bars[bars.index.get_level_values('timestamp').date == index.date()]

        up_to = bars[bars.index.get_level_values('timestamp') <= index]
        if up_to.empty:
            print(f'No bars for filtered {data.symbol}')
            self.missing_bars.append(data.symbol)
            return None, None, 0
        contract_price = up_to['close'].iloc[-1]
        cost = contract_price * 100 * buy_qty

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
                'cost_basis': cost,
                'bought_at': index.astimezone(pytz.timezone('US/Eastern')),
                'qty': buy_qty,
                'market_value': cost,
                'unrealized_plpc': 0,
                'date_of': index.date()
            })
            print(f'Purchased {data.symbol} at {index} with close at {close}')
            self.purchased_series[symbol].append(index)
            self.account = self.account - cost 
            return position, bars, cost
        
        return None, None, 0

    def exit(self, p, symbol, reason, index, bar, underlying_bar) -> None:
        print(f'Sold {p.symbol} for {reason}')
        tel = {
            'contract': p.symbol,
            'strike_price': p.strike_price,
            'type': p.contract_type,
            'bought_price': p.cost_basis,
            'sold_price': float(p.market_value),
            'bought_at': p.bought_at,
            'sold_at': index.astimezone(pytz.timezone('US/Eastern')),
            'held_for': index - p.bought_at,
            'sold_for': reason,
            'pl': (float(p.market_value) - p.cost_basis),
            'qty': p.qty,
            'nvi': bar['nvi'],
            'pvi': bar['pvi'],
            'nvi_short': bar['nvi_short_trend'],
            'nvi_long': bar['nvi_long_trend'],
            'pvi_short': bar['pvi_short_trend'],
            'pvi_long': bar['pvi_long_trend'],
        }
        self.sell_series[symbol].append(index)
        self.telemetry.append(tel)
        pl = tel['sold_price'] - tel['bought_price']
        self.pl_series.append([tel['type'], pl])
        self.actions = self.actions + 1
        if pl > 0:
            self.correct_actions = self.correct_actions + 1
            self.correct_bars[symbol].append(underlying_bar)
        else:
            self.incorrect_bars[symbol].append(underlying_bar)
        self.total[symbol] = self.total[symbol] + (float(p.market_value) - p.cost_basis)
        tracker.clear(p.symbol)
        self.account = self.account + float(p.market_value)

    def backtest_symbols(self, strat, symbols, start_dt, end_dt, window, timeframe):
        for symbol in symbols:
            # Get all the bars in this time frame and look for my indicators
            bars_handlers = bars_data.BarData(symbol, start_dt - timedelta(days=30), end_dt, self.market_client)
            bars = bars_handlers.get_bars(window, timeframe)

            # Only do what we want
            bars = bars[bars.index.get_level_values('timestamp') >= start_dt]

            # Get just the ones we'd buy
            bars = strat.enter(bars)
            # Can ignore hold
            bars = bars[bars['signal'] != 'hold']

            # Need to know when we were holding so if a signal happens when holding we dont buy extra
            held_positions = []

            balance = 3000

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
                position, position_bars, cost = self.enter(symbol, row, row['signal'], 1)

                # Determine exit
                if position != None:
                    balance = balance - cost
                    entered = index[1]
                    reason = 'expired'
                    for pindex, prow in position_bars.iterrows():
                        print(f'Checking {position.symbol} at {pindex}')

                        mv = prow['close'] * 100

                        qty = float(position.qty)
                        mv = mv * qty
                        temp_balance = balance + mv
                        self.account_bars[symbol].append([len(self.account_bars[symbol]) + 1, temp_balance])
                        pld = features.get_percentage_diff(position.cost_basis, mv) / 100

                        position.unrealized_plpc = f'{pld}'
                        position.market_value = f'{mv}'

                        exit, reason = strat.exit(position, prow)
                        if exit:
                            #d = position_bars.loc[pindex:]
                            #pd.DataFrame(data=d).to_csv(f'../results/{position.symbol}_{math.floor(pld*100)}.csv', index=True)
                            break

                    self.exit(position, symbol, reason, pindex[1], prow, row)
                    self.returns[symbol].append([pindex[1].date(), mv - position.cost_basis])
                    balance = balance + float(position.market_value)
                    held_positions.append([entered, pindex[1]])

    def run(self, show_graph = True) -> int:
        start_dt = self.start
        end_dt = self.end

        start_dt = start_dt.replace(hour=23, minute=59, second=0, microsecond=0) 
        start_dt = pytz.UTC.localize(start_dt)

        print(f'Back test from {start_dt} to {end_dt}')


        print(f'Running shorts')
        self.backtest_symbols(short_option.ShortOption(), self.shorts, start_dt, end_dt, 1, 'Min')

        print(f'Running longs')
        self.backtest_symbols(long_option.LongOption(), self.longs, start_dt, end_dt, 1, 'Hour')

        full_total = 0
        for cs in self.symbols:
            full_total = full_total + self.total[cs]
            print(f'{cs} total {self.total[cs]}')

        accuracy = 0
        if self.actions > 0:
            accuracy = self.correct_actions/self.actions
            print(f'Accuracy {accuracy} total {full_total} with {self.actions} actions')
        
        if len(self.positions) > 0:
            for p in self.positions:
                print(f'Still holding {p.symbol} with pl {p.unrealized_plpc}')

        print(f'Tried to buy {len(self.missing_bars)} but lacked data')

        sharpes = {}
        pd.DataFrame(data=self.telemetry).to_csv(f'../results/short_backtest_{self.start.strftime("%Y_%m_%d")}_{self.end.strftime("%Y_%m_%d")}.csv', index=True)
        for symbol in self.symbols:
            pd.DataFrame(data=self.correct_bars[symbol]).to_csv(f'../results/short_backtest_{self.start.strftime("%Y_%m_%d")}_{self.end.strftime("%Y_%m_%d")}_correct_bars.csv', index=True)
            pd.DataFrame(data=self.incorrect_bars[symbol]).to_csv(f'../results/short_backtest_{self.start.strftime("%Y_%m_%d")}_{self.end.strftime("%Y_%m_%d")}_incorrect_bars.csv', index=True)


            # add missing dates
            date_range = pd.date_range(start=self.start.date(), end=self.end.date(), freq='D')
            for dt in date_range:
                self.returns[symbol].append([dt.date(), 0])

            df = pd.DataFrame(data=self.returns[symbol], columns=['dates', 'returns'])
            df = df.groupby('dates').sum()
            risk_free_rate = 0.044
            excess_returns = df['returns'] - (risk_free_rate / 252) 
            mean_excess_return = excess_returns.mean() 
            std_excess_return = excess_returns.std() 
            sharpe_ratio = (mean_excess_return / std_excess_return) * np.sqrt(252) 
            sharpes[symbol] = sharpe_ratio
            print(f"{symbol} sharpe Ratio: {sharpe_ratio}")

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

            fig = plt.figure(2)

            for symbol in self.symbols:
                x = [s[0] for s in self.account_bars[symbol]]
                d = [s[1] for s in self.account_bars[symbol]]
                plt.plot(x, d, label=symbol) 

            plt.legend() 
            plt.title('Account balance per symbol') 
            plt.xlabel('Bar') 
            plt.ylabel('$') 

            # Show the plot
            plt.show()
        
        return full_total, accuracy, sharpes