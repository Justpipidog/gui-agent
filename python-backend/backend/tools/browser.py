"""浏览器自动化工具

包含执行 JavaScript 和获取浏览器状态两个工具。
这些工具在后端只作为占位符定义，真正执行由前端 LangGraph JS SDK 拦截。
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


class ExecuteJSInput(BaseModel):
    """execute_javascript 工具的参数模式"""

    description: str = Field(
        ...,
        description="你想做什么？（描述你的操作意图）",
    )
    js_code: str = Field(
        ...,
        description="""要执行的 JavaScript 代码。代码必须包含一个 main 函数。

        示例:
        async function main(context) {
            // 在这里编写你的所有逻辑
            // 你可以使用 context 中的快捷方式
            const log = "";
            log += "Hello world";
            return log;
        }
        """,
    )
    wait_after_run: Optional[int] = Field(
        default=2,
        description="执行后等待 X 秒",
    )
    wait_before_run: Optional[int] = Field(
        default=0,
        description="执行前等待 X 秒",
    )


class GetBrowserStateInput(BaseModel):
    """get_browser_state 工具的参数模式"""

    description: str = Field(
        ...,
        description="你想获取什么浏览器信息",
    )


@tool("execute_javascript", args_schema=ExecuteJSInput)
def execute_javascript(
    description: str,
    js_code: str,
    wait_after_run: Optional[int] = 2,
    wait_before_run: Optional[int] = 0,
) -> str:
    """
    在当前页面执行 JavaScript 代码，支持 async/await。谨慎使用！

    你的 JS 代码必须包含 main 函数：

    async function main(context) {
        // 所有逻辑写在这里
        // 可使用 context 快捷方式
        const log = "";
        log += "Hello world";
        return log;
    }
    """
    # 后端占位符，前端 LangGraph JS SDK 拦截执行
    return f"""JS 执行待前端处理：
- 描述: {description}
- 代码: {js_code[:100]}...
- 前等待: {wait_before_run}s
- 后等待: {wait_after_run}s
"""


@tool("get_browser_state", args_schema=GetBrowserStateInput)
def get_browser_state(description: str) -> str:
    """根据需求获取浏览器状态"""
    print(f"获取浏览器状态: {description}")
    return f'根据"{description}"获取浏览器状态: 占位实现'


# 工具列表
tools = [execute_javascript, get_browser_state]
