from __future__ import annotations

import logging
import os
from typing import Optional

_LOGGER_CONFIGURED = False


def _configure_root_logger(level: Optional[str]) -> None:
    global _LOGGER_CONFIGURED
    if _LOGGER_CONFIGURED:
        return
    resolved_level = getattr(logging, (level or "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    env_level = os.getenv("LOG_LEVEL")
    _configure_root_logger(env_level)
    return logging.getLogger(name)
