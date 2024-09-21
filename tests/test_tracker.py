from src.helpers import tracker

import unittest

class TestTracker(unittest.TestCase):

    def setUp(self):
        for i in range(100):
            tracker.track('QQQ', 0.01 + (i / 100), i)
            tracker.track('SPY', 0.01 + (i / 100), i)

    def test_tracker_last(self):
        hst = tracker.get('SPY')
        assert hst.iloc[-1]['market_value'] == 99

    def test_tracker_clears(self):
        tracker.clear('QQQ')

        hst = tracker.get('QQQ')

        assert hst.empty == True

if __name__ == '__main__':
    unittest.main()