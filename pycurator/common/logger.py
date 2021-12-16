"""Functions for instantiating logger and overriding uncaught exceptions to log files."""

from datetime import datetime
import logging
from pathlib import Path
import sys
from types import TracebackType
from typing import Type

from gunicorn import glogging


class GunicornLogger(glogging.Logger):  # type: ignore
    """Logger for Gunicorn."""

    def now(self) -> str:
        """Redefine method to get time format that is consistent.

        Returns:
            Formatted timestamp.
        """
        return datetime.now().strftime("[%Y-%m-%d %H:%M:%S,%f")[:-3] + "]"


def logging_exception_hook(
    exc_type: Type[BaseException], value: BaseException, track_back: TracebackType
) -> None:
    """Returns response from entity-fisher post request.

    Returns:
        A Response
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, value, track_back)
        return
    logging.error("Uncaught Exception", exc_info=(exc_type, value, track_back))


def return_logger(log_file: Path) -> logging.Logger:
    """Returns response from entity-fisher post request.

    Returns:
        A Response
    """
    log_formatter = "[%(asctime)s] [%(levelname)s] %(message)s"
    logging.basicConfig(
        format=log_formatter,
        level=logging.DEBUG,
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
    )
    return logging.getLogger(__name__)


sys.excepthook = logging_exception_hook


if __name__ == "__main__":
    logger = return_logger(Path("logs/logger_test.log"))
    logger.info("Here is some info")
    logger.debug("Here is some debugging too")
    raise RuntimeError("Testing hook")
