from datetime import datetime, time, timezone, timedelta
from src.strategies import short_signal, trending_model, option_exit
from src.helpers import options, features, tracker, get_data

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math

class BacktestOptionShort:

    def __init__(self, symbols, end, days, buy_amount, day_diff, market_client, trading_client, option_client) -> None:
        self.symbols = symbols
        self.end = end
        self.start = end - timedelta(days=days)
        self.market_client = market_client
        self.trading_client = trading_client
        self.option_client = option_client
        self.buy_qty = buy_amount 
        self.day_diff = day_diff
        self.option_exit = option_exit.OptionExit(trading_client)
        self.close_series = {}
        self.purchased_series = {}
        self.sell_series = {}
        self.pl_series = []
        self.telemetry = []
        self.positions = []
        self.actions = 0
        self.correct_actions = 0
        self.total = {}

        for s in self.symbols:
            self.close_series[s] = []
            self.purchased_series[s] = []
            self.sell_series[s] = []
            self.total[s] = 0

    def enter(self, symbol, row, signal, enter) -> None:
        index = row.name

        market_open = datetime.combine(index, time(13, 30), timezone.utc)
        market_close = datetime.combine(index, time(19, 1), timezone.utc)

        if index <= market_open or index >= market_close:
            return

        close = row['close']
        self.close_series[symbol].append([index, close])

        strike_price = math.floor(close)

        if enter:
            type = 'P'
            contract_type = 'put'
            if signal == 'buy':
                type = 'C'
                contract_type = 'call'

            contract_symbol = options.create_option_symbol(symbol, index if symbol == 'QQQ' or symbol == 'SPY' else options.next_friday(index) , type, strike_price)

            bars = options.get_bars(contract_symbol, index - timedelta(hours=1), index, self.option_client)

            if bars.empty:
                print(f'No bars for {contract_symbol}')
                return

            contract_price = bars['close'].iloc[-1] * self.buy_qty

            if contract_price > 0:
                class DotAccessibleDict:
                    def __init__(self, **entries):
                        self.__dict__.update(entries)
                self.positions.append(DotAccessibleDict(**{
                    'symbol': contract_symbol,
                    'contract_type': contract_type,
                    'strike_price': strike_price,
                    'close': close,
                    'price': contract_price,
                    'cost_basis': contract_price * 100,
                    'bought_at': index,
                    'qty': self.buy_qty,
                    'market_value': contract_price * 100,
                    'unrealized_plpc': 0,
                    'date_of': index.date()
                }))
                print(f'Purchased {contract_symbol} at {index}')
                self.purchased_series[symbol].append(index)

    def exit(self, p, exit, reason, close, mv, index, pl, symbol) -> None:
        if exit:
            print(f'Sold {symbol} for {reason}')
            tel = {
                'symbol': symbol,
                'contract': p.symbol,
                'strike_price': p.strike_price,
                'sold_close': close,
                'bought_close': p.close,
                'type': p.contract_type,
                'bought_price': p.cost_basis,
                'sold_price': mv,
                'bought_at': p.bought_at,
                'sold_at': index,
                'held_for': index - p.bought_at,
                'sold_for': reason,
                'pl': (mv - p.cost_basis)
            }
            self.sell_series[symbol].append(index)
            self.telemetry.append(tel)
            self.pl_series.append([tel['type'], (tel['sold_price'] - tel['bought_price'])])
            self.actions = self.actions + 1
            if pl > 0 or mv == 0:
                self.correct_actions = self.correct_actions + 1
            self.total[symbol] = self.total[symbol] + (mv - p.cost_basis)
            self.positions.remove(p)
            tracker.clear(p.symbol)

    def check_positions(self, index, last_close, symbol, signal, p_st, p_end, force_exit) -> None:
        filtered_positions = [p for p in self.positions if options.get_underlying_symbol(p.symbol) == symbol]
        for p in filtered_positions:
            print(f'Getting option bars for {p.symbol} days {p_st} to {p_end}')
            bars = options.get_bars(p.symbol, p_st, p_end, self.option_client)

            if bars.empty:
                print('No option data')
                continue

            dte = options.get_option_expiration_date(p.symbol)

            exit = False
            mv = float(p.market_value)
            plpc = float(p.unrealized_plpc)
            pl = mv + (plpc * mv)
            reason = ''

            # Option expired, sell it
            dt = index
            if dt.date() == dte.date() and dt.hour > 18:
                exit = True
                reason = 'expired'
            if dt.hour == 19 and (p.symbol == 'SPY' or p.symbol == 'QQQ'):
                exit = True
                reason = 'exit before close'
            if force_exit:
                exit = True
                reason = 'up to date'

            if exit == False:
                b = bars[bars.index.get_level_values('timestamp') <= dt]
                if b.empty:
                    current_bar = bars.iloc[0]
                else:
                    current_bar = b.iloc[-1]
                if current_bar.name[1].date() != dt.date() or current_bar.name[1].date() > dt.date():
                    print(current_bar)
                    print(dt)
                    raise ValueError("Looking at the wrong date for the contract")
                mv = current_bar['close'] * 100

                qty = float(p.qty)
                mv = mv * qty
                pl = mv - p.cost_basis
                pld = features.get_percentage_diff(p.cost_basis, mv) / 100

                p.unrealized_plpc = f'{pld}'
            
                p.market_value = f'{mv}'

                self.option_exit.add_positions([p])
                self.option_exit.add_signals([{'symbol': symbol, 'signal': signal}])
                exits = self.option_exit.exit()
                if len(exits) > 0:
                    exit = exits[0][0]
                    reason = exits[0][1]

            self.exit(p, exit, reason, last_close, mv, dt, pl, symbol)

    def run(self, show_graph = True) -> None:
        start_dt = self.start
        end_dt = self.end

        print(f'Back test from {start_dt} to {end_dt}')

        on_day = start_dt

        # Loop every day generate a model for the day, then loop the days bars
        amt_days = (end_dt - start_dt).days

        for t in range(amt_days):
            if on_day.weekday() < 5:

                on_day = on_day.replace(hour=9, minute=30)

                for symbol in self.symbols:
                    signaler = short_signal.Short(symbol, self.market_client)
                    model_builder = trending_model.TrendingModel(symbol, self.market_client)

                    # Get the model bars
                    #b_st = on_day - timedelta(days=self.day_diff)
                    #b_end = (on_day - timedelta(days=1)).replace(hour=20, minute=0)
                    #print(f'Getting model bars from {b_st} to {b_end}')
                    #bars = get_data.get_bars(symbol, b_st, b_end, self.market_client)

                    # Build the model
                    #print(f'Generating model for day {on_day}')
                    #model_builder.add_bars(bars)
                    #model_builder.feature_engineer_bars()
                    #model_builder.classify()

                    # Get the signal bars
                    b_st = on_day - timedelta(days=self.day_diff)
                    b_end = on_day.replace(hour=20, minute=0)
                    print(f'Getting days bars from {b_st} to {b_end}')
                    bars = get_data.get_bars(symbol, b_st, b_end, self.market_client)
                    bars = features.feature_engineer_df(bars)

                    #signaler.add_model(model_builder.generate_model())

                    # Just get the bars for the day
                    dtstr = on_day.strftime("%Y-%m-%d")
                    day_bars = bars.loc[(symbol, dtstr)]

                    for index in range(len(day_bars)): 
                        row = day_bars.iloc[[index]]
                        # Build the signaler to determine entry
                        signaler.add_bars(bars.loc[:(symbol, row.index[0])])
                        signaler.add_positions(self.positions)

                        enter, signal = signaler.signal()

                        self.enter(symbol, row.iloc[0], signal, enter)

                        self.check_positions(row.index[0], row.iloc[0]['close'], symbol, signal, on_day.replace(hour=9), row.index[0], False)

            on_day = on_day + timedelta(days=1)

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

        pd.DataFrame(data=self.telemetry).to_csv(f'../results/short_backtest.csv', index=True)

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