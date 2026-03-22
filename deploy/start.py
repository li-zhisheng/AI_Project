import time
import schedule
import yaml
import sys
import os
# 获取当前脚本所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 获取项目根目录
project_root = os.path.dirname(current_dir)
# 将项目根目录加入搜索路径
if project_root not in sys.path:
    sys.path.insert(0,project_root)
from core.logger import logger
from projects.auto_report.auto_report import main

# 加载配置
def load_config():
    try:
        with open("config.yaml","r",encoding="utf-8") as f:
            config = yaml.safe_load(f)
            if not config:
                raise ValueError("配置文件为空")
            return config
    except FileNotFoundError:
        logger.critical("配置文件config.yaml未找到，程序退出")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.critical(f"配置文件解析失败：{e}",exc_info=True)
        sys.exit(1)
    except Exception as e:
        logger.critical(f"加载配置时发生未知错误：{e}",exc_info=True)
        sys.exit(1)

# 定时任务
def job():
    logger.info("定时任务触发")
    try:
        main()
        logger.info("每日自动化报告执行完成")
    except Exception as e:
        logger.error(f"任务执行失败：{e}",exc_info=True)

# 启动定时
def start_scheduler(config):
    run_time = config["schedule"]["run_time"]
    schedule.every().day.at(run_time).do(job)
    logger.info(f"定时任务已启动，每天{run_time}自动执行")
    logger.info("进入等待模式")
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止服务")
    except Exception as e:
        logger.critical(f"调度器发生严重异常{e}",exc_info=True)

if __name__ == "__main__":
    config = load_config()
    logger.info(f"{config['app_name']} 启动成功")
    if config["schedule"]["enable"]:
        start_scheduler(config)
    else:
        logger.warning("定时功能已关闭，正在执行测试运行...")
        job()
        logger.info("测试运行结束，程序退出")