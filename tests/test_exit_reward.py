from src.strats import exit
from src.helpers import tracker

import unittest

class TestExitReward(unittest.TestCase):

    def setUp(self):
        self.contract = 'call'
        for r in range(10):
            tracker.track(self.contract, 0.01 * r, 10 + r)
        is_exit, reason = exit.check_reward_tolerance(tracker.get(self.contract), 19, 10)
        assert is_exit == False

    def test_decreased_slope_exit(self):
        tracker.track(self.contract, 0.065, 19.10)
        tracker.track(self.contract, 0.06, 19.15)
        # Slope is much slower
        tracker.track(self.contract, 0.07, 19.2)
        tracker.track(self.contract, 0.071, 19.21)
        is_exit, reason = exit.check_reward_tolerance(tracker.get(self.contract), 19.17, 10)
        assert is_exit == True
        assert reason == exit.slope_loss_reason

    def test_large_perc_diff(self):
        hst = tracker.get(self.contract)
        is_exit, reason = exit.check_reward_tolerance(hst, 18, 10)
        assert is_exit == True
        assert reason == exit.perc_diff_loss_reason

        is_exit, reason = exit.check_reward_tolerance(hst, 18.40, 10)
        assert is_exit == True
        assert reason == exit.perc_diff_loss_reason

        is_exit, reason = exit.check_reward_tolerance(hst, 18.50, 10)
        assert is_exit == False


if __name__ == '__main__':
    unittest.main()