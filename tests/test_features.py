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

if __name__ == '__main__':
    unittest.main()