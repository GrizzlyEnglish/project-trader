from src.helpers import features

import unittest
import pandas as pd

class TestFeatures(unittest.TestCase):

    def test_runnup_should_be_one_if_positive_runnup(self):
        cols = ['close', 'close_0_next', 'close_1_next','close_2_next','close_3_next']
        arr = [[40, 41, 41.4, 41.5, 42]]
        df = pd.DataFrame(data=arr, columns=cols)
        run = features.runnup(df, 'close', 4, 'next', True, False, False)
        assert run == 1

    def test_runnup_should_be_minus_one_if_negative_runnup(self):
        cols = ['close', 'close_0_next', 'close_1_next','close_2_next','close_3_next']
        arr = [[42, 41.5, 41.2, 41, 40]]
        df = pd.DataFrame(data=arr, columns=cols)
        run = features.runnup(df, 'close', 4, 'next', True, False, False)
        assert run == -1

    def test_percent_diff(self):
        pld = features.get_percentage_diff(60, 0) / 100
        assert pld == -1.0
        pld = features.get_percentage_diff(60, 24) / 100
        assert pld == -0.60
        pld = features.get_percentage_diff(60, 30) / 100
        assert pld == -0.50
        pld = features.get_percentage_diff(60, 90) / 100
        assert pld == 0.50
        pld = features.get_percentage_diff(60, 84) / 100
        assert pld == 0.40

if __name__ == '__main__':
    unittest.main()