from src.strategies import trending_model, option_exit, short_signal
from src.helpers import get_data, tracker
from src.options import sell, buy
from datetime import timedelta, datetime

class Short_Strat:

    def __init__(self, symbols, day_diff, market_client, trading_client, option_client) -> None:
        self.market_client = market_client
        self.trading_client = trading_client
        self.option_client = option_client
        self.symbols = symbols
        self.models = []
        self.day_diff = day_diff
        self.seller = sell.Sell(trading_client, option_client)
        self.buyer = buy.Buy(trading_client, option_client)

    def create_models(self, end):
        m_st = end - timedelta(days=self.day_diff-1)
        m_end = end

        for symbol in self.symbols:
            model = trending_model.TrendingModel(symbol, self.market_client)
            bars = get_data.get_bars(symbol, m_st, m_end, self.market_client, 1, 'Min')
            model.add_bars(bars)
            model.feature_engineer_bars()
            model.classify()
            m = model.generate_model()
            self.models.append({
                'symbol': symbol,
                'model': m
            })

    def check_enter(self) -> None:
        m_end = datetime.now() + timedelta(days=1)
        m_st = m_end - timedelta(days=self.day_diff)
        positions = get_data.get_positions(self.trading_client)

        for m in self.models:
            bars = get_data.get_model_bars(m['symbol'], self.market_client, m_st, m_end, 1, None, 'Min')
            close = bars.iloc[-1]['close'] 
            time = bars[-1:].index[0][1]

            signaler = short_signal.Short(m['symbol'], self.market_client)

            signaler.add_bars(bars)
            signaler.add_model(m['model'])
            signaler.add_positions(positions)
            signaler.feature_engineer_bars()

            enter, signal = signaler.signal()

            print(f'{m["symbol"]}: {time} {signal}')

            if enter:
                c = {
                    'symbol': m['symbol'],
                    'signal': signal,
                }
                self.buyer.purchase(c, close)

    def check_exit(self) -> None:
        positions = get_data.get_option_positions(self.trading_client)
        option_strat = option_exit.OptionExit(self.trading_client)
        option_strat.add_positions(positions)
        # TODO: add actual signals?
        option_strat.add_signals([])
        exits = option_strat.exit()
        for p in exits:
            print(f'Exiting {p.symbol} due to {p[1]}')
            self.seller.exit(p[0], p[1])
            tracker.clear(p.symbol)