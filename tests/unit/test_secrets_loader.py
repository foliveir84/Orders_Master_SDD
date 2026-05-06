import os
import unittest
from unittest.mock import patch

from orders_master.secrets_loader import get_secret


class TestSecretsLoader(unittest.TestCase):

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_priority_streamlit(self, mock_st_secrets, mock_os_getenv):
        """Tests if st.secrets has priority over environment variables."""
        # Mock st.secrets as a nested dict-like object
        mock_st_secrets.__getitem__.side_effect = lambda k: {
            "google_sheets": {"shortages_url": "st_url"}
        }[k]
        # In the actual implementation, it's accessed like st.secrets["key"]["subkey"]
        # The implementation uses for loop to navigate key_path.split(".")

        # Adjust mock for nested access
        mock_st_secrets.__getitem__.side_effect = None
        mock_st_secrets.__getitem__.return_value = {"shortages_url": "st_url"}

        mock_os_getenv.return_value = "env_url"

        # Test
        val = get_secret("google_sheets.shortages_url", "SHORTAGES_URL")
        self.assertEqual(val, "st_url")

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_fallback_to_env(self, mock_st_secrets, mock_os_getenv):
        """Tests if it falls back to environment variables when streamlit is missing."""
        # Simulate streamlit.secrets missing or causing error
        mock_st_secrets.__getitem__.side_effect = KeyError("Not found")
        mock_os_getenv.return_value = "env_url"

        val = get_secret("google_sheets.shortages_url", "SHORTAGES_URL")
        self.assertEqual(val, "env_url")

    @patch("os.getenv")
    def test_get_secret_default_env_name(self, mock_os_getenv):
        """Tests if it generates the correct default environment variable name."""

        # Use a side_effect to return values only for specific keys
        def side_effect(key, default=None):
            if key == "GOOGLE_SHEETS_SHORTAGES_URL":
                return "env_val"
            return os.environ.get(key, default)

        mock_os_getenv.side_effect = side_effect

        # Should look for "GOOGLE_SHEETS_SHORTAGES_URL"
        val = get_secret("google_sheets.shortages_url")
        self.assertEqual(val, "env_val")
        mock_os_getenv.assert_any_call("GOOGLE_SHEETS_SHORTAGES_URL")

    @patch("os.getenv")
    @patch("streamlit.secrets", create=True)
    def test_get_secret_none_if_missing(self, mock_st_secrets, mock_os_getenv):
        """Tests if it returns None if not found anywhere."""
        mock_st_secrets.__getitem__.side_effect = KeyError()
        mock_os_getenv.return_value = None

        val = get_secret("not.exists", "NOT_EXISTS")
        self.assertIsNone(val)


if __name__ == "__main__":
    unittest.main()
