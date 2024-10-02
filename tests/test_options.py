from src.helpers import options

import unittest

class TestOptions(unittest.TestCase):

    def test_risk_reward_values(self):
        stop_loss, secure_gains = options.determine_risk_reward(100)
        assert stop_loss == 70
        assert secure_gains == 190

        stop_loss, secure_gains = options.determine_risk_reward(400)
        assert stop_loss == 300
        assert secure_gains == 700

    def test_get_option_price(self):
        # Example QQQ
        S = 482.06  # Current stock price
        K = 481  # Strike price
        T_days = 3  # Time to expiration in days
        r = 0.05 # Risk-free interest rate

        call_price = options.get_option_price('call', S, K, T_days, r, 0.0568)
        put_price = options.get_option_price('put', S, K, T_days, r, 0.1495)

        assert round(call_price,2) == 1.74
        assert round(put_price,2) == 2.03

if __name__ == '__main__':
    unittest.main()