# Date    : 2024/7/5 18:00
# File    : utils.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import logging
from loguru import logger


class InterceptHandler(logging.Handler):
    """

    Args:
    Returns:
    Raises:
    """
    def emit(self, record: logging.LogRecord) -> None:
        """Get corresponding loguru level if it exists
        """
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = str(record.levelno)

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = cast(FrameType, frame.f_back)
            depth += 1

        # 格式化日志
        log_text = "{} - {}".format(record.levelname, record.getMessage())
        logger.opt(depth=depth, exception=record.exc_info).log(
            level, log_text,
        )


class NoLogInterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        pass


LOGGER_NAMES = ("uvicorn", "uvicorn.access", "python.nn_module",
                "huggingface_hub.hub_mixin",)

for logger_name in LOGGER_NAMES:
    other_logger = logging.getLogger(logger_name)

    # 使得logging的日志就会流到loguru进行处理
    if logger_name in ["huggingface_hub.hub_mixin",
                       "python.nn_module"]:
        other_logger.handlers = [NoLogInterceptHandler()]
    else:
        other_logger.handlers = [InterceptHandler()]


LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> " + \
             "| <level>{level}</level> " + \
             "| <cyan>{module}</cyan>:" + \
             "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

logger.remove()  # 移除默认的handler
logger.add('app.log', format=LOG_FORMAT, level="DEBUG", backtrace=True, diagnose=True)
