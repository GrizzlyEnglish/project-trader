from src.strats import exit
from src.helpers import tracker

import unittest

class TestExitRisk(unittest.TestCase):

    def test_risk_exit(self):
        is_exit, reason = exit.check_risk_tolerance(100, 150)
        assert is_exit == True
        assert reason == exit.stop_loss_reason

if __name__ == '__main__':
    unittest.main()