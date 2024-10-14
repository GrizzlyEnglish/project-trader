import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from datetime import timedelta
from src.strats import short
from src.helpers import get_data, class_model, features

import math

def backtest(start, end, backtest_func, market_client):
    # From the cut off date loop every day
    start_dt = start
    end_dt = end
    print(f'Back test from {start_dt} to {end_dt}')

    amt_days = (end - start).days
    loops = int(max(math.ceil(amt_days / 20), 1))

    p_st = start_dt

    for l in range(loops):
        p_end = p_st + timedelta(days=30)

        if p_end > end_dt:
            p_end = end_dt

        m_end = p_st - timedelta(days=1)

        print(f'Loop {l} from {p_st} to {p_end}')

        print(f'Generating model up to {m_end}')
        model_info = short.generate_short_models(market_client, m_end)

        for m in model_info:
            print(f'Classifying start {p_st} to {p_end}')
            pred_bars = get_data.get_bars(m['symbol'], p_st, p_end, market_client)
            pred_bars = features.feature_engineer_df(pred_bars)

            for index, row in pred_bars.iterrows():
                if index[1].date() < p_st.date():
                    continue

                h = pred_bars.loc[:index][-1:]

                enter, signal = short.do_enter(m['model'], h)

                backtest_func(m['symbol'], index, row, signal, enter, m)

        p_st = p_end 

        if p_st.date() >= end_dt.date():
            break