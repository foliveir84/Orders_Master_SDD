import logging
import unittest
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from orders_master.logger import SESSION_ID, configure_logging, timed


class TestLogger(unittest.TestCase):
    def test_session_id_exists(self):
        """Tests if SESSION_ID is a non-empty string."""
        self.assertTrue(isinstance(SESSION_ID, str))
        self.assertTrue(len(SESSION_ID) > 0)

    def test_configure_logging_setup(self):
        """Tests if configure_logging adds the correct handlers."""
        log_dir = Path("test_logs")

        # Clear existing handlers to bypass "if not root_logger.handlers" check
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        root_logger.handlers = []

        try:
            configure_logging(log_dir)

            handlers = root_logger.handlers

            # Check if we have at least TimedRotatingFileHandler and StreamHandler
            handler_types = [type(h) for h in handlers]
            self.assertIn(TimedRotatingFileHandler, handler_types)
            self.assertIn(logging.StreamHandler, handler_types)
        finally:
            # Clean up added handlers
            for h in root_logger.handlers:
                h.close()
            # Restore original handlers
            root_logger.handlers = original_handlers

            if log_dir.exists():
                for f in log_dir.iterdir():
                    f.unlink()
                log_dir.rmdir()

    def test_log_record_has_session_id(self):
        """Tests if log records have the session_id attribute injected by the filter."""
        logger = logging.getLogger("test_session_id")
        logger.setLevel(logging.DEBUG)

        # Use a mock handler to capture the log record
        class MockHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []

            def emit(self, record):
                self.records.append(record)

        mock_handler = MockHandler()
        from orders_master.logger import SessionFilter

        mock_handler.addFilter(SessionFilter())
        logger.addHandler(mock_handler)

        logger.info("Test message")

        self.assertEqual(len(mock_handler.records), 1)
        self.assertTrue(hasattr(mock_handler.records[0], "session_id"))
        self.assertEqual(mock_handler.records[0].session_id, SESSION_ID)

        logger.removeHandler(mock_handler)

    def test_timed_decorator(self):
        """Tests if the @timed decorator logs a message."""
        logger = logging.getLogger(__name__)

        class MockHandler(logging.Handler):
            def __init__(self):
                super().__init__()
                self.records = []

            def emit(self, record):
                self.records.append(record)

        mock_handler = MockHandler()
        logger.addHandler(mock_handler)
        logger.setLevel(logging.DEBUG)

        @timed
        def sample_func():
            return "done"

        # Overwrite the logger used inside @timed to point to this module's logger for testing
        # Actually, @timed uses logging.getLogger(func.__module__)
        # Since sample_func is in this module, it will use logging.getLogger(__name__)

        result = sample_func()

        self.assertEqual(result, "done")
        self.assertTrue(any("executed in" in r.getMessage() for r in mock_handler.records))

        logger.removeHandler(mock_handler)


if __name__ == "__main__":
    unittest.main()
