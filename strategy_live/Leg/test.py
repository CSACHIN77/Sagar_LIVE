import unittest
from LegUtil import get_strike  

class TestGetStrike(unittest.TestCase):
    def test_atm(self):
        # Test ATM case
        result = get_strike('ATM', 100, 3, 10)
        self.assertEqual(result, 100, "ATM case failed")

    def test_itm_call(self):
        # Test ITM case for Call Option (option_type = 3)
        result = get_strike('ITM2', 100, 3, 10)
        self.assertEqual(result, 80, "ITM Call case failed")

    def test_itm_put(self):
        # Test ITM case for Put Option (option_type != 3)
        result = get_strike('ITM2', 100, 4, 10)
        self.assertEqual(result, 120, "ITM Put case failed")

    def test_otm_call(self):
        # Test OTM case for Call Option (option_type = 3)
        result = get_strike('OTM2', 100, 3, 10)
        self.assertEqual(result, 120, "OTM Call case failed")

    def test_otm_put(self):
        # Test OTM case for Put Option (option_type != 3)
        result = get_strike('OTM2', 100, 4, 10)
        self.assertEqual(result, 80, "OTM Put case failed")

    def test_invalid_choice_value(self):
        # Test invalid choice_value
        with self.assertRaises(ValueError) as context:
            get_strike('INVALID', 100, 3, 10)
        self.assertEqual(str(context.exception), "Invalid choice_value: INVALID. Must be 'ATM', 'ITM', or 'OTM'.")

if __name__ == '__main__':
    unittest.main()
