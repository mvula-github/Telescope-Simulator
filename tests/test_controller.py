import unittest
from System_Checks import check_internet_connection, connection_message, NetworkStatus

class TestNetwork(unittest.TestCase):
    def test_network_status_shape(self):
        status = check_internet_connection(timeout=0.001)
        self.assertIsInstance(status, NetworkStatus)
        self.assertIsInstance(connection_message(status), str)

if __name__ == '__main__':
    unittest.main()
