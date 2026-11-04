import gzip
import logging
import logging.handlers
import os
import re
import shutil
from typing import ClassVar

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging(config: dict | None = None):
    config = config or {}
    log_level = config.get("level", logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # remove existing handlers to avoid duplicate logs in case of multiple calls to setup_logging
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(ColorFormatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S"
    ))
    console_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(console_handler)

    # 2. FILE LOGGING: daily rotate, compress, keep 5 files
    file_handler = GZipRotatingFileHandler(os.path.join(LOG_DIR, "app.log"),
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    file_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(file_handler)

    # 3. ERROR LOGGING: daily rotate, no compression, keep 30 days
    error_handler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(LOG_DIR, "errors.log"),
        when="midnight",
        interval=1,
        backupCount=30, # 30 giorni
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    error_handler.addFilter(SensitiveDataFilter())
    root_logger.addHandler(error_handler)


class SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""

    PATTERNS: ClassVar[tuple[str, ...]] = (
        r'password["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'token["\']?\s*[:=]\s*["\']?[^"\'\s]+',
        r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    )

    def __init__(self) -> None:
        super().__init__()
        self.compiled = tuple(
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.PATTERNS
        )

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for regex in self.compiled:
            msg = regex.sub("[REDACTED]", msg)
        record.msg = msg
        record.args = ()
        return True


class ColorFormatter(logging.Formatter):
    """color log levels"""
    COLORS: ClassVar[dict[int, str]] = {
        logging.DEBUG: "\033[36m",    # Cyan
        logging.INFO: "\033[32m",     # Green
        logging.WARNING: "\033[33m",  # Yellow
        logging.ERROR: "\033[31m",    # Red
        logging.CRITICAL: "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class GZipRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that compresses old log files with gzip."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def doRollover(self):
        # std rot
        super().doRollover()
        # zip the old log file
        for i in range(1, self.backupCount + 1):
            sfn = self.rotation_filename(f"{self.baseFilename}.{i}")
            if os.path.exists(sfn) and not sfn.endswith(".gz"):
                gz_fn = f"{sfn}.gz"
                try:
                    with open(sfn, "rb") as f_in, gzip.open(gz_fn, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    os.remove(sfn) # delete not compressed file
                except OSError as e:
                    # no logging here othwise recursion, just print to stderr
                    print(f"[GZipHandler ERROR] Compression failed for {sfn}: {e}")


