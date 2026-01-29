"""工作流业务逻辑 - Agent 创建和配置"""

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph_pro.hitl import HumanInTheLoopMiddleware
from backend.prompt import system_prompt
from backend.tools import tools
import os


async def create_workflow(state: MessagesState):
    """创建 LangGraph 工作流 - 包含 agent 和 middleware 配置"""

    # 从环境变量获取模型配置
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-4o")
    api_key = os.getenv("OPENAI_API_KEY", "")
    api_base = os.getenv("OPENAI_BASE_URL", "")

    # 创建模型
    model_kwargs = {
        "model": model_name,
        "api_key": api_key,
        "temperature": 0,
    }
    if api_base:
        model_kwargs["base_url"] = api_base

    model = ChatOpenAI(**model_kwargs)

    # 使用 create_agent 创建 agent
    graph = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
        state_schema=MessagesState,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    # ask_user_with_options 配置
                    "ask_user_with_options": {
                        "allowed_decisions": ["respond"],
                    },
                    # 自定义工具配置
                    "execute_javascript": {
                        "allowed_decisions": ["respond", "reject"],
                    },
                    "get_browser_state": {
                        "allowed_decisions": ["respond", "reject"],
                    },
                }
            )
        ],
    )

    response = await graph.ainvoke(state)
    return response
