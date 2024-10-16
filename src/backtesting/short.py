import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from datetime import timedelta
from src.strats import short
from src.helpers import get_data, class_model, features, options

import math

def backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions):
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

                enter, signal = short.do_enter(m['model'], h, m['symbol'], positions)

                backtest_enter(m['symbol'], index, row, signal, enter, m)
            
                for p in positions:
                    bars = options.get_bars(p.symbol, index[1] - timedelta(hours=1), index[1], option_client)
                    mv = 0
                    if not bars.empty:
                        mv = bars['close'].iloc[-1] * 100

                    pl = mv - p.p_market_value
                    pld = features.get_percentage_diff(p.p_market_value, mv, False) / 100

                    p.unrealized_plpc = f'{pld}'
                    p.market_value = f'{mv}'

                    exit, reason = short.do_exit(p, [{'symbol': m['symbol'], 'signal': signal}]) 

                    backtest_exit(p, exit, reason, row['close'], mv, index[1], pl, m['symbol'])

        p_st = p_end 

        if p_st.date() >= end_dt.date():
            break