from src.helpers import load_stocks, class_model, short_classifier, overnight_classifier
from datetime import datetime, timedelta
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.timeframe import TimeFrameUnit

import os
import unittest

load_dotenv()

api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")
paper = os.getenv("IS_PAPER")
sleep_time = os.getenv("SLEEP_TIME")

def save_bars(model_bars, name, symbol):
    b_bars = model_bars[model_bars['label'] == class_model.label_to_int('buy')]
    b_bars.to_csv(f'results/{symbol}_{name}_buy_signals.csv', index=True)

    s_bars = model_bars[model_bars['label'] == class_model.label_to_int('sell')]
    s_bars.to_csv(f'results/{symbol}_{name}_sell_signals.csv', index=True)

class TestModel(unittest.TestCase):

    def setUp(self):
        self.short_info = load_stocks.load_symbol_information('short_option_symbols.txt')
        self.overnight_info = load_stocks.load_symbol_information('overnight_option_symbols.txt')
        self.trading_client = TradingClient(api_key, api_secret, paper=paper)
        self.market_client = StockHistoricalDataClient(api_key, api_secret)
        self.start = datetime(2024, 9, 15, 12, 30)

    def test_short_classification_model_generation(self):
        for info in self.short_info:
            symbol = info['symbol']
            day_diff = info['day_diff']
            time_window = info['time_window']
            look_back = info['look_back']
            look_forward = info['look_forward']

            s = self.start - timedelta(days=day_diff)
            e = self.start + timedelta(days=1)

            timer_start = datetime.now()
            bars, call_var, put_var = class_model.get_model_bars(symbol, self.market_client, s, e, time_window, short_classifier.classification, look_back, look_forward, TimeFrameUnit.Minute)
            model, model_bars, arccuracy, buys, sells = class_model.generate_model(symbol, bars)

            save_bars(model_bars, 'short', symbol)

            timer_end = datetime.now()

            print(f'Took {symbol} {timer_end - timer_start}')

            assert model != None
            assert arccuracy > .7
            assert buys >= 100
            assert sells >= 100
    
    def test_overnight_classification_model_generation(self):
        for info in self.overnight_info:
            symbol = info['symbol']
            day_diff = info['day_diff']
            time_window = info['time_window']
            look_back = info['look_back']
            look_forward = info['look_forward']

            s = self.start - timedelta(days=day_diff)
            e = self.start + timedelta(days=1)

            timer_start = datetime.now()
            bars = class_model.get_model_bars(symbol, self.market_client, s, e, time_window, overnight_classifier.classification, look_back, look_forward, TimeFrameUnit.Hour)
            model, model_bars, arccuracy, buys, sells = class_model.generate_model(symbol, bars)

            save_bars(model_bars, 'overnight', symbol)

            timer_end = datetime.now()

            print(f'Took {symbol} {timer_end - timer_start}')

            assert model != None
            # TODO: This needs to be higher
            assert arccuracy > .5

if __name__ == '__main__':
    unittest.main()