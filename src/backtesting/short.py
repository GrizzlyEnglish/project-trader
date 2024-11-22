import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from datetime import timedelta
from src.strats import short
from src.helpers import get_data, class_model, features, options
from datetime import datetime

import math
import pandas as pd

option_bars = {}

def check_positions(positions, i, last_close, m, signal, p_st, p_end, option_client, backtest_exit, force_exit):
    for p in positions:
        if p.symbol in option_bars:
            bars = option_bars[p.symbol]
        else:
            oend = p_end
            if oend >= datetime.now():
                oend = datetime.now()
            print(f'Getting option bars for {p.symbol} days {p_st} to {oend}')
            bars = options.get_bars(p.symbol, p_st, oend, option_client)
            option_bars[p.symbol] = bars

        if bars.empty:
            print('No option data')
            continue

        dte = options.get_option_expiration_date(p.symbol)

        exit = False
        mv = float(p.market_value)
        plpc = float(p.unrealized_plpc)
        pl = mv + (plpc * mv)

        # Option expired, sell it
        if i[1].date() == dte.date() and i[1].hour > 18:
            exit = True
            reason = 'expired'
        if i[1].hour == 19:
            exit = True
            reason = 'exit before close'
        if force_exit:
            exit = True
            reason = 'Up to date'

        if exit == False:
            b = bars[bars.index.get_level_values('timestamp') <= i[1]]
            if b.empty:
                mv = bars.iloc[0]['close'] * 100
            else:
                mv = b.iloc[-1]['close'] * 100

            qty = float(p.qty)
            mv = mv * qty
            pl = mv - p.cost_basis
            pld = features.get_percentage_diff(p.cost_basis, mv) / 100

            p.unrealized_plpc = f'{pld}'
        
            p.market_value = f'{mv}'
            exit, reason = short.do_exit(p, [{'symbol': m['symbol'], 'signal': signal}]) 

        backtest_exit(p, exit, reason, last_close, mv, i[1], pl, m['symbol'])

def backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions):
    day_diff = int(os.getenv('DAYDIFF'))
    # From the cut off date loop every day
    start_dt = start
    end_dt = end
    print(f'Back test from {start_dt} to {end_dt}')

    on_day = start_dt

    # Loop every day generate a model for the day, then loop the days bars
    amt_days = (end - start).days
    for t in range(amt_days):
        if on_day.weekday() < 5:

            print(f'Generating model for day {on_day}')
            model_info = short.generate_short_models(market_client, on_day - timedelta(days=1))

            for m in model_info:
                print(f'Classifying start {on_day} for {m["symbol"]}')
                pred_bars = get_data.get_bars(m['symbol'], on_day - timedelta(days=day_diff), on_day + timedelta(days=1), market_client)
                pred_bars = features.feature_engineer_df(pred_bars)
                held_bars = pred_bars.copy()
                indexes = pred_bars.index
                pred_bars = class_model.preprocess_bars(pred_bars)

                for index,h in enumerate(pred_bars):
                    i = indexes[index]

                    if i[1].date() < on_day.date() or i[1].date() > on_day.date():
                        continue

                    row = held_bars.loc[i]
                    indicator = features.my_indicator(row)
                    enter, signal = short.do_enter(m['model'], [h], m['symbol'], positions, indicator)

                    backtest_enter(m['symbol'], i, row, signal, enter, m)

                    check_positions(positions, i, row['close'], m, signal, on_day - timedelta(days=1), on_day + timedelta(days=1), option_client, backtest_exit, False)

        on_day = on_day + timedelta(days=1)