import logging

from logging.handlers import TimedRotatingFileHandler

FORMATTER = '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
LOG_FILE = 'matcher.log'
ROLLOVER_INTERVAL = 'midnight'


def get_formatter() -> logging.Formatter:
    formatter = logging.Formatter(FORMATTER)
    return formatter


def get_file_handler() -> logging.FileHandler:
    file_handler = TimedRotatingFileHandler(LOG_FILE, when=ROLLOVER_INTERVAL)
    file_handler.setFormatter(get_formatter())
    return file_handler


def get_logger(name: str = __name__, level: int = logging.DEBUG) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(get_file_handler())
    return logger
