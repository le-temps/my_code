import sys
from loguru import logger

logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD at HH:mm:ss}</green> | <level>{message}</level>")