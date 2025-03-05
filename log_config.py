# log_config.py  
import logging  
import os  
from datetime import datetime


current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def setup_logging(log_dir):  
    # 创建logger  
    logger = logging.getLogger('MaaS_test')  
    logger.setLevel(logging.DEBUG)  
  
    # 创建handler来写入日志文件  
    # log_dir = 'logs'  
    if not os.path.exists(log_dir):  
        os.makedirs(log_dir)  
    log_path = os.path.join(log_dir, 'MaaS_test_{}.log'.format(current_time))  
    file_handler = logging.FileHandler(log_path, encoding='utf-8')  
    file_handler.setLevel(logging.DEBUG)  
  
    # 创建handler来将日志输出到控制台  
    console_handler = logging.StreamHandler()  
    console_handler.setLevel(logging.INFO)  
  
    # 定义handler的输出格式  
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  
    file_handler.setFormatter(formatter)  
    console_handler.setFormatter(formatter)  
  
    # 给logger添加handler  
    logger.addHandler(file_handler)  
    logger.addHandler(console_handler)  
  
    return logger