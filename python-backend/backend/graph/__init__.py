"""LangGraph 工作流入口 - 只负责组合，不含业务逻辑"""

from langgraph.graph import StateGraph, START, END, MessagesState
from backend.graph.workflow import create_workflow

# 构建 Graph
agent = (
    StateGraph(MessagesState)
    .add_node("workflow", create_workflow)
    .add_edge(START, "workflow")
    .add_edge("workflow", END)
    .compile()
)
