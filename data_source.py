"""祈福签数据源模块"""

from datetime import datetime
from pathlib import Path
from nonebot_plugin_uninfo import Uninfo

from zhenxun.configs.path_config import DATA_PATH
from zhenxun.utils.platform import PlatformUtils

from .src.render import BlessingRenderer

# 祈福签图片存储路径
BLESSING_CARD_PATH = DATA_PATH / "blessing_sign"


class BlessingManage:
    """祈福签管理类"""

    @classmethod
    async def draw(cls, session: Uninfo, assets_dir: str) -> Path:
        """抽签

        参数:
            session: Uninfo
            assets_dir: 资源目录路径

        返回:
            Path: 签图路径
        """
        import pytz
        
        platform = PlatformUtils.get_platform(session)
        user_id = session.user.id
        now = datetime.now(pytz.timezone("Asia/Shanghai"))
        
        # 检查是否已有当天的签
        file_name = f"{user_id}_{now.date()}.png"
        card_file = BLESSING_CARD_PATH / file_name
        
        if card_file.exists():
            return card_file
        
        # 生成新的签
        return await cls._generate_blessing_image(user_id, now, assets_dir)

    @classmethod
    async def _generate_blessing_image(
        cls, user_id: str, now: datetime, assets_dir: str
    ) -> Path:
        """生成祈福签图片

        参数:
            user_id: 用户ID
            now: 当前日期时间
            assets_dir: 资源目录路径

        返回:
            Path: 生成的图片路径
        """
        BLESSING_CARD_PATH.mkdir(exist_ok=True, parents=True)
        
        # 构造渲染器配置
        config = {
            "image": {
                "width": 1240,
                "height": 620,
                "font_size": 40,
                "assets_dir": assets_dir,
            }
        }

        renderer = BlessingRenderer(config)
        img_bytes = renderer.generate_blessing_image()

        # 保存图片
        file_name = f"{user_id}_{now.date()}.png"
        card_file = BLESSING_CARD_PATH / file_name
        
        with open(card_file, "wb") as f:
            f.write(img_bytes)
        
        return card_file
