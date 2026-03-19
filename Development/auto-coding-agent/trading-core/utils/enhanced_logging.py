"""
日志系统增强 - 结构化日志、聚合、查询
简单实现:结构化日志、日志级别、文件轮转
"""
from loguru import logger
import sys

# 配置增强日志
logger.remove()
logger.add(sys.stderr, level="INFO", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("logs/trading.log", rotation="1 day", retention="30 days", level="DEBUG")
