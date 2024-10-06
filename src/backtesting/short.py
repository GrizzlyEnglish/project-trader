import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from datetime import timedelta
from alpaca.data.timeframe import TimeFrameUnit
from src.helpers.load_parameters import load_symbol_parameters
from src.helpers import get_data, features
from src.strats import short_enter

import math

def backtest(start, end, backtest_func, market_client):
    params = load_symbol_parameters('../params.json')

    # From the cut off date loop every day
    start_dt = start
    end_dt = end
    print(f'Predict start {start_dt} model end {end_dt}')

    amt_days = (end - start).days
    loops = int(max(math.ceil(amt_days / 20), 1))

    p_st = start_dt

    for l in range(loops):
        p_end = p_st + timedelta(days=30)

        print(f'Loop {l} on start {p_st} model end {p_end}')
        if p_end > end_dt:
            p_end = end_dt

        m_end = p_end - timedelta(days=1)

        print(f'Generating model up to {m_end}')
        model_info = short_enter.generate_short_models(market_client, m_end, '../params.json')

        for m in model_info:
            symbol = m['symbol']
            p = m['params']

            day_diff = p['runnup']['day_diff']
            if p['runnup']['day_diff'] != p['dip']['day_diff'] or p['runnup']['look_back'] != p['dip']['look_back']:
                print("Params dont match might get slightly weird results")

            print(f'Predicting start {p_end - timedelta(days=day_diff)}-{p_st}-{p_end}')
            pred_bars = get_data.get_bars(symbol, p_end - timedelta(days=day_diff), p_end, market_client, p['runnup']['time_window'], p['runnup']['time_unit'])

            dip_pred_bars = features.feature_engineer_df(pred_bars.copy(), p['dip']['look_back'])
            dip_pred_bars = features.drop_prices(dip_pred_bars, p['dip']['look_back'])

            runnup_pred_bars = features.feature_engineer_df(pred_bars.copy(), p['runnup']['look_back'])
            runnup_pred_bars = features.drop_prices(runnup_pred_bars, p['runnup']['look_back'])

            for index, row in pred_bars.iterrows():
                if index[1].date() < p_st.date():
                    continue

                dp_h = dip_pred_bars.loc[index:][:1]
                run_h = runnup_pred_bars.loc[:index][-2:]

                signals = short_enter.classify_short_signal(dp_h, run_h, m)

                backtest_func(symbol, index, row, signals, m)

        p_st = p_end 

        if p_st > end_dt:
            break