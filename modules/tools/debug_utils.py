import os
import sys
from loguru import logger

# 环境变量 JWXT_DEBUG 控制是否开启 DEBUG
DEBUG = os.getenv("JWXT_DEBUG", "").lower() in ("1", "true", "yes")

# 日志文件名（相对路径）
LOG_PATH = os.path.join(os.getcwd(), "auto_course.log")

def init_logger(debug_flag: bool) -> str:
    """
    初始化 Loguru 日志：
      - 控制台输出（stderr）
      - 文件输出（auto_course.log），10 MB 分割，保留 3 个归档
    :param debug_flag: 是否开启 DEBUG 级别
    :return: 日志文件完整路径
    """
    level = "DEBUG" if debug_flag else "INFO"
    # 先移除任何已有的 sink
    logger.remove()
    # 控制台
    logger.add(
        sink=sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level:<8}</level> | "
               "{message}"
    )
    # 文件
    logger.add(
        sink=LOG_PATH,
        level=level,
        rotation="10 MB",     # 日志文件达到 10MB 时分割
        retention=3,          # 保留最近 3 个归档
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} - {message}"
    )
    logger.debug("日志初始化完成，级别：{}", level)
    return LOG_PATH