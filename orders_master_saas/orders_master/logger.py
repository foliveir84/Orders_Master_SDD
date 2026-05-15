import logging
import time
import uuid
from collections.abc import Callable
from functools import wraps
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, TypeVar

# Session ID unique for each execution session
SESSION_ID = str(uuid.uuid4())

F = TypeVar("F", bound=Callable[..., Any])


class SessionFilter(logging.Filter):
    """
    Filter that injects the session_id into log records.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.session_id = SESSION_ID
        return True


def timed(func: F) -> F:
    """
    Decorator that logs the execution time of a function at DEBUG level.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = logging.getLogger(func.__module__)
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        duration = end_time - start_time
        logger.debug(f"Function '{func.__name__}' executed in {duration:.4f} seconds")
        return result

    return wrapper  # type: ignore


def configure_logging(log_dir: Path = Path("logs")) -> None:
    """
    Configures centralized logging with a rotating file handler and a stream handler.

    Args:
        log_dir (Path): Directory where log files will be stored.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "orders_master.log"

    # Base configuration
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(session_id)s | %(name)s | %(message)s"
    )

    # Rotating File Handler (Daily, 7 backups)
    file_handler = TimedRotatingFileHandler(
        log_file, when="D", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(SessionFilter())

    # Stream Handler (Stdout)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(SessionFilter())

    # Root Logger Configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if configure_logging is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)
        root_logger.addHandler(stream_handler)

    # Specialized logger for orders_master
    om_logger = logging.getLogger("orders_master")
    om_logger.setLevel(logging.DEBUG)  # More verbose for our internal modules
