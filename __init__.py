import base64
from pathlib import Path
from annotated_types import T
from nonebot import get_driver
from nonebot.plugin import PluginMetadata
from zhenxun.utils.message import MessageUtils
from zhenxun.configs.utils import PluginExtraData, Command, PluginCdBlock
from zhenxun.utils.enum import PluginType
from zhenxun.services.log import logger
from nonebot_plugin_uninfo import Uninfo
from nonebot_plugin_alconna import (
    on_alconna, 
    Alconna,
)

from .src.render import BlessingRenderer
from .data_source import BlessingManage
from .utils import clear_blessing_data_pic

dir_path = Path(__file__).parent

ASSETS_DIR = str((dir_path / "assets").absolute())

__plugin_meta__ = PluginMetadata(
    name="祈福签",
    description="基于 skyblessings-python-api 的祈福签生成插件",
    usage="""
    指令：
        祈福签/祈福/skyblessings/抽签
    每个人每天只能抽一次，多次抽签会返回当天的签
    """,
    extra=PluginExtraData(
        author="影灵3",
        version="0.1",
        plugin_type=PluginType.NORMAL,
        menu_type="光遇",
        commands=[
            Command(command="祈福签"),
            Command(command="祈福"),
            Command(command="skyblessings"),
            Command(command="抽签"),
        ],
        limits=[PluginCdBlock()],
    ).dict(),
)


blessing_cmd = on_alconna(Alconna(["", "/"], "祈福签"), aliases={"祈福", "skyblessings", "抽签"}, priority=5, block=True)

@blessing_cmd.handle()
async def _(session: Uninfo):
    try:
        # 调用数据源生成或获取签
        card_path = await BlessingManage.draw(session, ASSETS_DIR)
        
        # 读取图片文件
        with open(card_path, "rb") as f:
            img_data = f.read()
        
        # 转为 base64 并发送
        b64 = base64.b64encode(img_data).decode("utf-8")
        await MessageUtils.build_message(f"base64://{b64}").send(reply_to=True)
        
        logger.info(f"祈福签抽签成功", "祈福签", session=session)
    except Exception as e:
        logger.error(f"祈福签生成失败: {e}", "祈福签")
        await MessageUtils.build_message("生成祈福签失败").send()


driver = get_driver()


@driver.on_startup
async def init_blessing():
    """初始化祈福签数据"""
    from zhenxun.configs.path_config import DATA_PATH
    blessing_path = DATA_PATH / "blessing_sign"
    blessing_path.mkdir(exist_ok=True, parents=True)
    clear_blessing_data_pic()
    logger.info("祈福签初始化完成", "祈福签")


try:
    from nonebot_plugin_apscheduler import scheduler

    @scheduler.scheduled_job(
        "interval",
        hours=6,
    )
    async def _():
        """每6小时清理一次过期的祈福签图片"""
        try:
            clear_blessing_data_pic()
        except Exception as e:
            logger.error(f"清理祈福签图片失败: {e}", "祈福签")
except ImportError:
    logger.warning("nonebot_plugin_apscheduler 未安装，自动清理功能不可用", "祈福签")
