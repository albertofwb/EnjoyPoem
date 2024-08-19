import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from time import time, strftime, localtime


logger_name = "console"


def get_current_time():
    fmt = '%Y-%m-%d %H:%M:%S'
    return strftime(fmt, localtime(time()))


def epoch_to_localhost(epoch_time: float) -> str:
    return strftime('%Y-%m-%d %H:%M:%S', localtime(epoch_time))


def get_logger(logger_name: str, log_file: str = None) -> logging.Logger:
    logger = logging.getLogger(logger_name)

    # 检查logger是否已经有处理器，如果有，直接返回
    if logger.handlers:
        return logger

    FMT = logging.Formatter("%(asctime)s %(levelname)s %(filename)s:%(lineno)s %(message)s")
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FMT)
    # File handler (if log_file is provided)
    if log_file:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # Create a RotatingFileHandler
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(FMT)
        logger.addHandler(file_handler)

    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)

    # 防止日志传播到根日志器
    logger.propagate = False

    return logger


def extended_seconds_to_hms(seconds) -> str:
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    if days > 0:
        return f"{int(days):d}:{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    else:
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
