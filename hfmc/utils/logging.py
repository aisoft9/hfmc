"""Logging utils."""

import argparse
import logging
import logging.handlers
import sys

from hfmc.common.context import HfmcContext
from hfmc.utils import args as arg_utils


def _create_stream_handler(level: int) -> logging.Handler:
    """Create a stream handler."""
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(level)
    return handler


def _create_file_handler(level: int) -> logging.Handler:
    """Create a file handler."""
    log_dir = HfmcContext.get_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "hfmc.log"

    handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
    )

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handler.setFormatter(logging.Formatter(log_format))
    handler.setLevel(level)

    return handler


def setup_logging(args: argparse.Namespace) -> None:
    """Set up logging."""
    # configure root logger
    level = arg_utils.get_logging_level(args)

    if arg_utils.is_detached_daemon(args):
        handler = _create_file_handler(level)
    else:
        handler = _create_stream_handler(level)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # suppress lib's info log
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("filelock").setLevel(logging.WARNING)
    logging.getLogger("huggingface_hub").setLevel(logging.WARNING)
