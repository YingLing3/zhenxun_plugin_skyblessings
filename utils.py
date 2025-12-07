"""祈福签工具模块"""

import os
from datetime import datetime, timedelta
from pathlib import Path

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.services.log import logger

# 祈福签图片存储路径
BLESSING_CARD_PATH = DATA_PATH / "blessing_sign"


def clear_blessing_data_pic():
    """清理超过7天的祈福签图片"""
    if not BLESSING_CARD_PATH.exists():
        return
    
    now = datetime.now()
    deleted_count = 0
    
    for file_path in BLESSING_CARD_PATH.glob("*.png"):
        try:
            # 获取文件修改时间
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            # 如果文件超过7天，删除
            if (now - file_mtime) > timedelta(days=7):
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            logger.error(f"删除祈福签图片失败: {file_path}, {e}")
    
    if deleted_count > 0:
        logger.info(f"清理祈福签图片完成，共删除 {deleted_count} 张过期图片", "祈福签")
