# logging setup

import logging
import logging.handlers

def setup_logger(level: int=logging.DEBUG):
    logger = logging.getLogger('discord')

    logger.setLevel(logging.DEBUG)
    logging.getLogger('discord.http').setLevel(logging.INFO)

    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{')

    rf_handler = logging.handlers.RotatingFileHandler(
        filename='discord.log',
        encoding='utf-8',
        maxBytes=32 * 1024 * 1024,  # 32 MiB
        backupCount=5,  # Rotate through 5 files
    )

    s_handler = logging.StreamHandler()

    for handler in [rf_handler, s_handler]:
        handler.setFormatter(formatter)
        handler.setLevel(level)

        logger.addHandler(handler)

    return logger

logger = setup_logger(logging.DEBUG)