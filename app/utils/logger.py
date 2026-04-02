import logging
import sys
import json
from datetime import datetime, timezone
from app.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    """Return a logger that writes JSON to stdout and logs/app.log."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # avoid duplicate handlers

    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    fmt = JSONFormatter()

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler (created lazily)
    try:
        fh = logging.FileHandler("logs/app.log", encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass  # logs/ dir may not exist in some test environments

    return logger
