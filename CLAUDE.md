# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 语言
所有对话必须使用中文回答

## 权限
你可以直接编辑文件、运行脚本，无需经过我的同意

## 项目概述

Page-Six Agent LangGraph 是一个通过自然语言聊天实现远程网页控制的浏览器自动化系统。项目包含两个主要后端实现（TypeScript 和 Python）以及一个 SolidJS 前端。

**核心技术栈：**
- **LangGraph** - AI agent 编排，支持人工干预
- **SolidJS** - 响应式前端框架
- **RxDB** - 客户端持久化 (IndexedDB)
- **Hono** - 轻量级 API 服务
- **FastAPI** - Python 后端 API 服务
- **@page-agent/page-controller** - 浏览器自动化

## 项目结构

```
page-agent-langgraph/
├── page-six-agent/           # TypeScript 版本 (PNPM monorepo)
│   ├── packages/
│   │   ├── page-agent-server/   # LangGraph 后端 (Bun + Hono)
│   │   │   └── src/
│   │   │       ├── graph/        # LangGraph 工作流定义
│   │   │       ├── prompt/       # 中文系统提示词
│   │   │       ├── tools/        # 工具定义 (execute_javascript, get_browser_state)
│   │   │       └── frontend/     # PageAgentContext, shortcuts, tool registration
│   │   └── solid-ui/             # SolidJS 前端 (Vite)
│   │       └── src/components/
│   │           ├── chat/         # 聊天 UI (MagicChat, MessageList, ChatInput)
│   │           └── gateway/      # 网关管理 UI
│   │               └── db/        # RxDB 数据库层 (routes, logs, settings)
│
├── python-backend/           # Python 版本
│   ├── backend/
│   │   ├── main.py              # FastAPI 主应用入口
│   │   └── utils.py             # 前端工具处理、JavaScript 执行等
│   ├── .env.example             # 环境变量模板
│   ├── pyproject.toml           # Python 依赖配置
│   └── run_server.py            # 服务器启动脚本
│
└── package.json               # 根目录依赖 (tsx)
```

## 开发命令

### TypeScript 后端 (Bun + Hono)
```bash
cd page-six-agent/packages/page-agent-server
bun run dev       # 启动 Hono 服务器 (默认端口 8123)
```

### Python 后端 (FastAPI)
```bash
cd python-backend

# 使用 uv 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 LLM_MODEL_NAME 和 OPENAI_API_KEY

# 启动服务器
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
# 或使用提供的脚本
python run_server.py
```

### 前端 (SolidJS + Vite)
```bash
cd page-six-agent/packages/solid-ui
pnpm dev          # 启动 Vite 开发服务器 (默认端口 5173)
pnpm build        # TypeScript 编译 + Vite 构建
pnpm preview      # 预览生产构建
```

### 安装依赖
```bash
# 根目录
pnpm install      # 安装 tsx 等工具
```

## LangGraph 架构

### TypeScript 版本
- 文件: `page-six-agent/packages/page-agent-server/src/graph/index.ts`
- 使用 `StateGraph` 配合 `MessagesAnnotation`
- 单节点 "workflow" 包装 `createAgent()` 调用
- 模型: `ChatOpenAI` 使用 `qwen-plus`
- 工具: `execute_javascript`, `get_browser_state`
- 人工干预机制: 工具执行时中断 (respond/reject)

### Python 版本
- 文件: `python-backend/backend/main.py`
- 使用 FastAPI + LangGraph
- 兼容 LangGraph JS SDK 的 API 接口
- 支持会话状态管理和检查点系统
- 工具定义与前端执行分离
- API 端点:
  - `POST /v1beta/graphs/page-agent/runs` - 创建运行实例
  - `GET /v1beta/graphs/page-agent/runs/{run_id}` - 获取运行状态
  - `GET /graph/assistants/search` - 列出/搜索助手
  - `WS /ws/{thread_id}` - WebSocket 实时通信

## 浏览器自动化模式

页面交互使用基于快捷方式的 JavaScript 执行：

1. **`get_browser_state`** 分析 DOM 并为交互元素分配索引
2. Agent 使用快捷方式编写 JavaScript 代码：
   - `context.shortcuts.click_element_by_index(index)`
   - `context.shortcuts.fill_input(index, text)`
   - `context.shortcuts.getBrowserState()`
3. 代码通过 `execute_javascript` 工具执行
4. Agent 验证结果并继续工作流

参考 `page-six-agent/packages/page-agent-server/src/frontend/shortcut.ts` 查看可用快捷方式。

## RxDB 数据库模块

网关 UI 使用 RxDB 15.x 进行客户端持久化。数据模型：
- **routes** - API 路由定义（状态和请求计数）
- **logs** - HTTP 请求日志（方法、路径、状态、延迟）
- **settings** - 单例配置（网关名称、超时、认证、限流）

关键 API (`page-six-agent/packages/solid-ui/src/components/gateway/db/`)：
- `getAllRoutes()`, `createRoute()`, `updateRoute()`, `toggleRouteStatus()`
- `queryLogs(filters)`, `createLog()`, `clearAllLogs()`
- `getSettings()`, `updateSettings()`, `resetSettings()`

**重要**: 使用数据库的每个组件必须调用 `useDatabase()` hook 进行初始化。

## 系统提示词

Agent 使用中文系统提示词 (`page-six-agent/packages/page-agent-server/src/prompt/system_prompt.ts`)：
- 人设: "远程网页操作助手"
- 使命: 通过主动探索实现用户满意度
- 回复格式: 仅纯文本（无 Markdown），水平数据格式化
- 工作流: 观察 → 分析 → 规划 → 执行 → 验证
- 模糊指令处理: 必须先探索当前页面再询问澄清

## Vite 配置

前端 Vite 配置 (`page-six-agent/packages/solid-ui/vite.config.ts`)：
- 代理: `/api/langgraph` → `http://localhost:8123`（TypeScript 后端）
- 代理: `/api/langgraph` → `http://localhost:8000`（Python 后端）
- 别名: `page-agent` → `../page-agent-server/frontend`
- TailwindCSS 4.x 通过 `@tailwindcss/vite` 集成

## 类型安全

- TypeScript 版本使用 Zod v4 进行验证 (`page-agent-server`)
- Python 版本使用 Pydantic 进行数据验证
- 前后端均采用严格类型模式
- RxDB schemas 定义在 `page-six-agent/packages/solid-ui/src/components/gateway/db/schema.ts`

## 人工干预 (Human-in-the-Loop)

系统支持关键操作的人工确认机制：
- Agent 自主规划动作，但执行需要用户批准
- 前端可以通过 WebSocket `/ws/{thread_id}` 发送工具执行结果
- 支持中断-恢复机制，确保敏感操作的安全性
