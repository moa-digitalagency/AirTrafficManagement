import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add repo root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.invoice_generator import get_contact_phone

class TestInvoiceConfig(unittest.TestCase):

    @patch('services.invoice_generator.SystemConfig')
    def test_get_contact_phone_exists(self, mock_system_config):
        # Setup mock return value
        mock_config_entry = MagicMock()
        mock_config_entry.value = "+243 999 888 777"

        # Configure the query chain
        mock_system_config.query.filter_by.return_value.first.return_value = mock_config_entry

        # Call function
        phone = get_contact_phone()

        # Verify
        self.assertEqual(phone, "+243 999 888 777")
        mock_system_config.query.filter_by.assert_called_with(key='rva_contact_phone')

    @patch('services.invoice_generator.SystemConfig')
    def test_get_contact_phone_missing(self, mock_system_config):
        # Setup mock to return None
        mock_system_config.query.filter_by.return_value.first.return_value = None

        # Call function
        phone = get_contact_phone()

        # Verify fallback
        self.assertEqual(phone, "+2431234567890")
        mock_system_config.query.filter_by.assert_called_with(key='rva_contact_phone')

if __name__ == '__main__':
    unittest.main()
