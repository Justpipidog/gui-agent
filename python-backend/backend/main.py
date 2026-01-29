"""FastAPI 应用入口"""

import asyncio
import logging
import sys

from dotenv import load_dotenv
from langgraph_server import cli

load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Windows 事件循环策略
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


if __name__ == "__main__":
    cli.main()
