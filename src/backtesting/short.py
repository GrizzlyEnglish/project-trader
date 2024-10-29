import os,sys
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from datetime import timedelta
from src.strats import short
from src.helpers import get_data, class_model, features, options
from datetime import datetime

import math

def backtest(start, end, backtest_enter, backtest_exit, market_client, option_client, positions):
    group = int(os.getenv('BAR_GROUP'))
    day_diff = int(os.getenv('DAYDIFF'))
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

        option_bars = {}

        for m in model_info:
            print(f'Classifying start {p_st} to {p_end}')
            pred_bars = get_data.get_bars(m['symbol'], p_st - timedelta(days=day_diff), p_end, market_client)
            pred_bars = features.feature_engineer_df(pred_bars)

            for index, row in pred_bars.iterrows():
                pb = pred_bars.loc[:index]

                if index[1].date() < p_st.date() or len(pb) < 5:
                    continue

                h = pb[-group-1:]

                enter, signal = short.do_enter(m['model'], h, m['symbol'], positions)

                backtest_enter(m['symbol'], index, row, signal, enter, m)
            
                for p in positions:
                    if p.symbol in option_bars:
                        bars = option_bars[p.symbol]
                    else:
                        oend = p_end
                        if oend >= datetime.now():
                            oend = datetime.now()
                        bars = options.get_bars(p.symbol, p_st, oend, option_client)
                        option_bars[p.symbol] = bars

                    if bars.empty:
                        print('No option data')
                        continue

                    dte = options.get_option_expiration_date(p.symbol)

                    # Option expired, sell it
                    if index[1].date() == dte.date() and index[1].hour > 18:
                        mv = float(p.market_value)
                        exit = True
                        reason = 'expired'
                    else:
                        b = bars[bars.index.get_level_values('timestamp') <= index[1]]
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

                    backtest_exit(p, exit, reason, row['close'], mv, index[1], pl, m['symbol'])

        p_st = p_end 

        if p_st.date() >= end_dt.date():
            break