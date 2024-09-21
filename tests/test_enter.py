from src.strats import enter

import unittest

class TestEnter(unittest.TestCase):

    def test_enter_contract_moves_enough(self):
        enter_contract, price = enter.check_contract_entry('contract', 'call', 481, 1.98, 1.94, 0.0568, 3, 482.06, 0.005)
        assert enter_contract == True

    def test_enter_contract_doesnt_move_enough(self):
        enter_contract, price = enter.check_contract_entry('contract', 'call', 481, 1.98, 1.94, 0.0568, 3, 482.06, 0.001)
        assert enter_contract == False

    def test_enter_contract_moves_enough_but_dte_too_far(self):
        enter_contract, price = enter.check_contract_entry('contract', 'call', 481, 3.98, 3.94, 0.0568, 14, 482.06, 0.005)
        assert enter_contract == False

    def test_enter_contract_moves_enough_but_iv_crush(self):
        enter_contract, price = enter.check_contract_entry('contract', 'call', 481, 22.98, 22.94, 0.568, 14, 482.06, 0.005)
        assert enter_contract == False

if __name__ == '__main__':
    unittest.main()