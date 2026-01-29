# Page-Agent-LangGraph 系统架构文档

## 1. 项目概述

`page-agent-langgraph` 是一个基于 LangGraph 构建的智能页面代理系统，结合前端 UI 与后端逻辑，支持通过自然语言与网页进行交互，执行 JavaScript 工具操作等任务。

**目标用户**: 前端开发者、AI Agent 研究者、自动化测试人员

**核心功能**:
- 实现对网页内容的理解与交互控制
- 提供可视化聊天界面用于调试和使用 AI Agent
- 支持快捷指令与工具调用（如执行 JS 脚本）

## 2. 系统架构

### 2.1 整体架构图

```
[Browser UI (solid-ui)] 
        ⇄ HTTP/WebSocket 
[Vite Proxy → Hono 服务器]
        ⇄ LangGraph 工作流
        ⇄ 工具执行 (Human-in-the-Loop)
        ⇄ 状态管理 (检查点系统)
```

### 2.2 技术选型

- **前端**: SolidJS + Vite + TypeScript
- **后端**: TypeScript + Hono + LangGraph
- **构建工具**: pnpm
- **样式**: Tailwind CSS

## 3. 关键模块及其交互逻辑

### 3.1 前端 UI 模块 (solid-ui)

**组件**: [ChatProvider](file://d:\code\page-agent-langgraph\page-six-agent\packages\solid-ui\src\components\chat\MagicChat.tsx#L34-L40)、[MagicChat](file://d:\code\page-agent-langgraph\page-six-agent\packages\solid-ui\src\components\chat\MagicChat.tsx#L58-L70)、各种聊天组件

**功能**: 提供用户交互界面，处理用户输入和结果显示

**交互逻辑**:
- 用户在 UI 中输入问题或指令
- 通过 `@langgraph-js/sdk/solid` 的 [ChatProvider](file://d:\code\page-agent-langgraph\page-six-agent\packages\solid-ui\src\components\chat\MagicChat.tsx#L34-L40) 发送请求
- Vite 代理将 `/api/langgraph` 请求转发到后端 Hono 服务器

### 3.2 代理与构建模块 (Vite)

**组件**: [vite.config.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\solid-ui\vite.config.ts)

**功能**: 开发时的请求代理和前端构建

**交互逻辑**:
- 将前端的 `/api/langgraph` 请求代理到 `http://localhost:8123`（后端 Hono 服务器）
- 重写路径，移除前缀，确保请求正确到达后端路由

### 3.3 后端服务器模块 (Hono)

**组件**: [src/index.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src/index.ts)

**功能**: HTTP 请求处理和路由

**交互逻辑**:
- 通过 `app.route('/', LangGraphApp)` 将所有根路径请求交给 LangGraph 应用处理
- 生成 API 端点（如 `/graph/assistants`、`/messages` 等）

### 3.4 工作流注册模块

**组件**: [registerGraph('graph', graph)](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\index.ts#L7-L7)

**功能**: 注册 LangGraph 工作流

**交互逻辑**:
- 注册名为 'graph' 的工作流实例
- 使工作流可通过 API 端点访问（如 `/graph/assistants/graph`）

### 3.5 LangGraph 工作流模块

**组件**: [graph/index.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\graph\index.ts)

**功能**: AI 推理、工具调用和状态管理

**交互逻辑**:
- 接收用户消息并进行 AI 推理
- 根据需要决定是否调用工具（如 [execute_javascript](file://d:\code\page-agent-langgraph\python-backend\backend\main.py#L28-L54)、[get_browser_state](file://d:\code\page-agent-langgraph\python-backend\backend\main.py#L52-L55)）
- 应用 `humanInTheLoopMiddleware` 实现中断机制

### 3.6 工具定义模块

**组件**: [tools/excute-js.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\tools\excute-js.ts)

**功能**: 定义可执行的工具

**交互逻辑**:
- 定义工具接口（名称、参数、描述）
- 与前端 UI 工具通过名称匹配实现具体执行逻辑

### 3.7 前端工具执行模块

**组件**: [frontend/tools.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\frontend\tools.ts)

**功能**: 在浏览器中执行工具

**交互逻辑**:
- 通过 `createUITool` 创建可交互的 UI 工具
- 检测 `tool.client.status === 'interrupted'` 和 `tool.state === 'interrupted'` 状态
- 在前端执行实际的浏览器操作
- 通过 `sendResumeData()` 将结果回传给后端

### 3.8 页面控制与上下文模块

**组件**: [frontend/index.ts](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\frontend\index.ts) 中的 [PageAgentContext](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\frontend\index.ts#L17-L59)

**功能**: 作为前端工具与浏览器控制层之间的桥梁

**交互逻辑**:
- 通过 [toSafeJSObject()](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\frontend\index.ts#L48-L57) 提供受控执行环境
- 绑定 [page](file://d:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server\src\frontend\index.ts#L19-L19) 控制器和快捷方式
- 管理工具和快捷方式的执行上下文

### 3.9 Human-in-the-Loop 机制

**交互流程**:
1. 后端中间件触发中断并保存执行状态
2. 发送包含工具名称、输入数据的中断事件
3. 前端 SDK 更新本地状态为 `interrupted`
4. UI 工具检测到中断状态后激活执行逻辑
5. 通过 `sendResumeData()` 恢复执行并同步结果

## 4. 数据流转路径

1. **用户输入** → 前端 UI → Vite 代理 → Hono 服务器 → LangGraph 工作流
2. **AI 推理** → 决定是否调用工具 → 触发 Human-in-the-Loop 机制
3. **工具中断** → 前端检测 → 执行浏览器操作 → 结果回传
4. **工作流恢复** → 继续执行 → 结果返回前端 → 渲染显示

## 5. 安全机制

- **工具执行需确认**：采用中断-恢复模式，确保敏感操作经过人工确认
- **受控执行环境**：通过 `toSafeJSObject()` 提供安全的执行环境
- **参数验证**：使用 Zod 验证工具参数的有效性
- **检查点系统**：使用 LangGraph 检查点功能，确保状态一致性

## 6. 设计模式

- **前后端分离架构**: 前端负责展示，后端处理业务逻辑与 AI 编排
- **工具定义与执行分离**: 后端定义工具接口，前端实现具体执行逻辑
- **事件驱动交互**: 用户输入触发 graph 流程执行
- **工具模式**: 将可执行动作封装为工具供 Agent 调用

## 7. 开发环境设置

```bash
# 安装依赖
pnpm install

# 启动前端 UI
cd page-six-agent/packages/solid-ui && pnpm dev

# 启动 Agent 服务器
cd page-six-agent/packages/page-agent-server && pnpm start
# 或使用 tsx 直接运行
npx tsx src/index.ts
```

## 8. 部署要求

- 前端构建命令:
  ```bash
  cd page-six-agent/packages/solid-ui
  pnpm build
  ```

- 部署目标: 静态站点 + Node.js API 服务