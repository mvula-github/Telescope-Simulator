import unittest
from System_Config import config
from Calculations import convert_radec_to_degrees
from Telescope_Movement import check_limits

class TestConfigAndConversions(unittest.TestCase):
    def test_config_validate(self):
        # validate returns bool; we just ensure it runs without exception
        self.assertIsInstance(config.validate(), bool)

    def test_convert_formats(self):
        ra_deg, dec_deg = convert_radec_to_degrees("00h42m30s", "+41d12m00s")
        self.assertIsInstance(ra_deg, float)
        self.assertIsInstance(dec_deg, float)

class TestMovementLimits(unittest.TestCase):
    def test_limits(self):
        # Values inside default limits
        self.assertTrue(check_limits(0, 180))
        # Values outside
        self.assertFalse(check_limits(-90, 0))

if __name__ == '__main__':
    unittest.main()
