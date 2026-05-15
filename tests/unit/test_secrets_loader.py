import os
import unittest
from unittest.mock import patch

from orders_master.secrets_loader import DONOTBUY_SHEET_URL, SHORTAGES_SHEET_URL, get_secret


class TestSecretsLoader(unittest.TestCase):

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_priority_streamlit(self, mock_st_secrets, mock_os_getenv):
        """Tests if st.secrets has priority over environment variables."""
        mock_st_secrets.__getitem__.return_value = "st_url"
        mock_os_getenv.return_value = "env_url"

        val = get_secret(SHORTAGES_SHEET_URL)
        self.assertEqual(val, "st_url")

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_fallback_to_env(self, mock_st_secrets, mock_os_getenv):
        """Tests if it falls back to environment variables when streamlit is missing."""
        mock_st_secrets.__getitem__.side_effect = KeyError("Not found")
        mock_os_getenv.return_value = "env_url"

        val = get_secret(SHORTAGES_SHEET_URL)
        self.assertEqual(val, "env_url")

    @patch("os.getenv")
    def test_get_secret_default_env_name(self, mock_os_getenv):
        """Tests if it uses the key as the env var name directly."""

        def side_effect(key, default=None):
            if key == SHORTAGES_SHEET_URL:
                return "env_val"
            return os.environ.get(key, default)

        mock_os_getenv.side_effect = side_effect

        val = get_secret(SHORTAGES_SHEET_URL)
        self.assertEqual(val, "env_val")
        mock_os_getenv.assert_any_call(SHORTAGES_SHEET_URL)

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_none_if_missing(self, mock_st_secrets, mock_os_getenv):
        """Tests if it returns None if not found anywhere."""
        mock_st_secrets.__getitem__.side_effect = KeyError()
        mock_os_getenv.return_value = None

        val = get_secret("NOT_EXISTS")
        self.assertIsNone(val)

    def test_standardized_key_names(self):
        """Tests that standardized key names are defined."""
        self.assertEqual(SHORTAGES_SHEET_URL, "SHORTAGES_SHEET_URL")
        self.assertEqual(DONOTBUY_SHEET_URL, "DONOTBUY_SHEET_URL")


if __name__ == "__main__":
    unittest.main()