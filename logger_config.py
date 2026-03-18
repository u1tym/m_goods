from __future__ import annotations

import logging
import os
from logging import Logger
from logging.handlers import TimedRotatingFileHandler


LOG_DIR_ENV_KEY = "M_GOODS_LOG_DIR"
DEFAULT_LOG_DIR = "logs"


def _ensure_log_dir() -> str:
    log_dir: str = os.getenv(LOG_DIR_ENV_KEY, DEFAULT_LOG_DIR)
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _create_root_logger() -> Logger:
    log_dir = _ensure_log_dir()
    logger = logging.getLogger("m_goods")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    log_path = os.path.join(log_dir, "app.log")
    handler = TimedRotatingFileHandler(
        filename=log_path,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s %(message)s",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


_ROOT_LOGGER: Logger = _create_root_logger()


def get_logger(name: str | None = None) -> Logger:
    """Return application logger (child logger when name is given)."""
    if not name:
        return _ROOT_LOGGER
    return _ROOT_LOGGER.getChild(name)

