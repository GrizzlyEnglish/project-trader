from src.classifiers import runnup, dip
from src.helpers import load_parameters
from src.helpers import class_model
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
        self.params = load_parameters.load_symbol_parameters()
        self.trading_client = TradingClient(api_key, api_secret, paper=paper)
        self.market_client = StockHistoricalDataClient(api_key, api_secret)
        self.start = datetime(2024, 9, 15, 12, 30)

    def test_runnup_classification_model_generation(self):
        for p in self.params:
            info = p['runnup']
            symbol = p['symbol']

            timer_start = datetime.now()
            model_info = class_model.generate_model(symbol, info, self.market_client, runnup.classification, self.start)

            save_bars(model_info['bars'], 'runnup', symbol)

            timer_end = datetime.now()

            print(f'Took {symbol} {timer_end - timer_start}')

            assert model_info['model'] != None
            assert model_info['accuracy'] > .7
            assert model_info['buys'] >= 100
            assert model_info['sells'] >= 100
    
    def test_dip_classification_model_generation(self):
        for p in self.params:
            symbol = p['symbol']
            info = p['dip']

            timer_start = datetime.now()
            model_info = class_model.generate_model(symbol, info, self.market_client, dip.classification, self.start)

            save_bars(model_info['bars'], 'dip', symbol)

            timer_end = datetime.now()

            print(f'Took {symbol} {timer_end - timer_start}')

            assert model_info['model'] != None
            assert model_info['accuracy'] > .6
            assert model_info['buys'] >= 100
            assert model_info['sells'] >= 100

if __name__ == '__main__':
    unittest.main()