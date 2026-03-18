# 日志工具
import logging
import os
from datetime import datetime

def get_logger(name="ai_project"):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 文件输出
    log_file = os.path.join(log_dir,f"{datetime.now().strftime('%Y-%m-%d')}.log")
    fh = logging.FileHandler(log_file,encoding="utf-8")
    fh.setFormatter(formatter)

    # 控制台输出
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = get_logger()