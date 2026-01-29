# Page-Six Agent 前后端交互架构说明

本文档详细描述了 Page-Six Agent 项目的通信机制和数据流，帮助开发者理解前端与后端 Agent 之间的交互方式。

## 1. 系统概述

Page-Six Agent 是一个通过自然语言聊天实现远程网页控制的浏览器自动化系统。

### 1.1 核心组件

| 组件 | 技术栈 | 职责 |
|------|--------|------|
| **SolidJS 前端** | Vite + SolidJS | 用户界面、消息展示、工具渲染 |
| **TypeScript 后端** | Bun + Hono + LangGraph | Agent 编排、工具定义、人机交互 |
| **Python 后端** | FastAPI + LangGraph | 替代后端实现，兼容前端 SDK |
| **Page Controller** | @page-agent/page-controller | 浏览器自动化底层操作 |

### 1.2 服务端口

| 服务 | 端口 | 地址 |
|------|------|------|
| SolidJS 前端 | 5173/5174 | http://localhost:5173 |
| TypeScript 后端 | 8123 | http://localhost:8123 |
| Python 后端 | 8000 | http://localhost:8000 |

---

## 2. 通信架构

### 2.1 整体数据流

```
┌────────────────────────────────────────────────────────────────────────┐
│                           完整通信流程                                  │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐     HTTP POST    ┌──────────────┐                   │
│  │   SolidJS    │ ───────────────▶ │   LangGraph  │                   │
│  │   前端       │   /stream        │   后端       │                   │
│  │              │ ◀─────────────── │              │                   │
│  └──────────────┘   SSE Stream     └──────────────┘                   │
│       ▲                              │                                  │
│       │                              │ 中断 (interrupt)                 │
│       │                              ▼                                  │
│  ┌──────────────┐   WebSocket       ┌──────────────┐                   │
│  │   前端工具   │ ◀───────────────▶ │  Human-in-   │                   │
│  │   执行层     │   工具调用/结果   │  the-Loop    │                   │
│  └──────────────┘                   └──────────────┘                   │
│       │                                                               │
│       ▼                                                               │
│  ┌──────────────┐                                                     │
│  │ Page-Agent   │  浏览器自动化 (点击、输入、获取状态)                 │
│  │ Controller   │                                                     │
│  └──────────────┘                                                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 通信协议

系统使用三种通信方式的组合：

| 协议 | 用途 | 数据格式 |
|------|------|----------|
| **HTTP POST** | 发送用户消息，创建运行实例 | JSON |
| **SSE (Server-Sent Events)** | 流式返回执行进度和消息更新 | `data: {...}` |
| **WebSocket** | 工具中断时的实时交互 | JSON 消息流 |

---

## 3. 前端到后端 API 调用

### 3.1 API 配置 (SolidJS)

前端使用 `@langgraph-js/sdk` 的 `ChatProvider` 组件配置与后端的连接：

**文件**: `packages/solid-ui/src/components/chat/MagicChat.tsx`

```typescript
export const MagicChat = () => {
    return (
        <ChatProvider
            apiUrl={new URL('/api/langgraph', location as any as string).toString()}
            showHistory={false}
            fallbackToAvailableAssistants={true}
        >
            <MagicChatContent />
        </ChatProvider>
    );
};
```

### 3.2 Vite 代理配置

**文件**: `packages/solid-ui/vite.config.ts`

```typescript
export default defineConfig({
    plugins: [solid(), tailwindcss()],
    server: {
        proxy: {
            '/api/langgraph': {
                target: 'http://localhost:8123',  // TypeScript 后端
                // 或 target: 'http://localhost:8000',  // Python 后端
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api\/langgraph/, ''),
            },
        },
    },
});
```

### 3.3 消息发送机制

**文件**: `packages/solid-ui/src/components/chat/ChatInput.tsx`

```typescript
const handleSendMessage = (content: string) => {
    chat.sendMessage([{ type: 'human', content }], {
        extraParams: { extraPrompt: getExtraPrompt() },
    });
};
```

前端通过 `useChat()` hook 发送消息，支持传递额外参数（如快捷方式提示）。

---

## 4. Agent 执行流程

### 4.1 TypeScript 后端 Graph 定义

**文件**: `packages/page-agent-server/src/graph/index.ts`

```typescript
const workflow = async (state: any) => {
    const agent = createAgent({
        model: new ChatOpenAI({
            model: 'qwen-plus',
            useResponsesApi: false,
        }),
        systemPrompt: system_prompt,
        tools: [execute_javascript, get_browser_state],
        middleware: [
            humanInTheLoopMiddleware({
                interruptOn: {
                    execute_javascript: { allowedDecisions: ['respond', 'reject'] },
                    get_browser_state: { allowedDecisions: ['respond', 'reject'] },
                },
            }),
        ],
        stateSchema: State,
    });
    const response = await agent.invoke(state);
    return response;
};

export const graph = new StateGraph(State)
    .addNode('workflow', workflow)
    .addEdge(START, 'workflow')
    .compile();
```

### 4.2 工具执行流程 (三阶段)

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Agent 工具执行流程                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  阶段 1: 消息发送                                                   │
│  ─────────────────                                                 │
│  前端调用: chat.sendMessage([{type: 'human', content: ...}])       │
│  后端接收用户消息，开始执行 LangGraph                               │
│                                                                     │
│  阶段 2: LLM 决策与工具中断                                         │
│  ─────────────────────────────                                     │
│  LLM 分析消息，决定调用工具 (如 get_browser_state)                  │
│  LangGraph 检测到工具调用 → 中断执行 (interrupt_before=["tools"])   │
│  返回工具调用信息给前端，等待确认                                   │
│                                                                     │
│  阶段 3: 前端工具渲染与恢复                                         │
│  ─────────────────────────                                         │
│  前端工具的 render() 方法被触发                                     │
│  前端执行实际浏览器操作 (通过 Page-Agent Controller)                │
│  操作完成后调用 tool.sendResumeData() 恢复后端执行                 │
│                                                                     │
│  阶段 4: 结果处理                                                   │
│  ─────────────────                                                 │
│  后端接收工具执行结果，继续 LangGraph 执行                          │
│  LLM 分析结果，决定下一步操作或返回最终答案                         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Human-in-the-Loop 机制

```typescript
// 后端配置中断策略
humanInTheLoopMiddleware({
    interruptOn: {
        execute_javascript: { allowedDecisions: ['respond', 'reject'] },
        get_browser_state: { allowedDecisions: ['respond', 'reject'] },
    },
})
```

| 决策 | 说明 |
|------|------|
| **respond** | 接受工具执行结果，继续执行 |
| **reject** | 拒绝当前操作，可重新规划 |

---

## 5. 工具定义与执行

### 5.1 工具注册 (前端)

**文件**: `packages/solid-ui/src/components/chat/tools.ts`

```typescript
import { PageAgentContext } from '../../../../page-agent-server/src/frontend';

export const pageAgent = new PageAgentContext({});
pageAgent.initShortcuts();

export const registerTools = () => {
    return [...pageAgent.initTools()];
};
```

### 5.2 工具定义 (后端)

**文件**: `packages/page-agent-server/src/frontend/tools.ts`

```typescript
export const createExecuteJSTool = (client: PageAgentContext) => {
    return createUITool({
        name: 'execute_javascript',
        parameters: {
            js_code: z.string(),
            wait_after_run: z.number().optional().default(2),
            wait_before_run: z.number().optional().default(0),
        },
        handler: ToolManager.waitForUIDone,
        render(tool) {
            if (tool.client.status === 'interrupted' && tool.state === 'interrupted') {
                // 执行实际的 JavaScript 代码
                const mainFunction = eval(code);
                const actionResult = await mainFunction(client.toSafeJSObject());
                // 恢复执行
                tool.sendResumeData({ type: 'respond', message: JSON.stringify(actionResult) });
            }
        },
    });
};
```

### 5.3 可用快捷方式

**文件**: `packages/page-agent-server/src/frontend/shortcut.ts`

| 快捷方式 | 说明 |
|----------|------|
| `click_element_by_index(index)` | 点击指定索引的元素 |
| `fill_input(index, text)` | 在指定索引输入框填写文本 |
| `getBrowserState()` | 获取当前浏览器状态和页面信息 |
| `getCurrentUrl()` | 获取当前页面 URL |
| `getPageTitle()` | 获取页面标题 |
| `getPageInfo()` | 获取页面结构化信息 |
| `getSimplifiedHTML()` | 获取简化后的 HTML |

### 5.4 浏览器状态获取

`getBrowserState()` 返回格式化的页面描述：

```markdown
当前页面信息:
- URL: https://example.com
- 标题: 示例网站

可交互元素 (按索引):
[0] 链接 - "关于我们" (href: /about)
[1] 按钮 - "搜索" (type: submit)
[2] 输入框 - 搜索关键词 (placeholder: 请输入...)
[3] 下拉菜单 - 选择分类
...
```

---

## 6. 消息类型定义

### 6.1 三种消息类型

**文件**: `packages/solid-ui/src/components/chat/MessageItem.tsx`

| 类型 | 说明 | 示例 |
|------|------|------|
| **human** | 用户发送的消息 | "帮我点击搜索按钮" |
| **ai** | AI 助手生成的消息 | "我来帮您操作..." |
| **tool** | 工具执行结果 | `{tool: "click", result: "success"}` |

### 6.2 消息数据结构

```typescript
interface Message {
    type: 'human' | 'ai' | 'tool';
    content: string;
    tool_calls?: Array<{
        name: string;
        arguments: Record<string, any>;
    }>;
    tool_results?: Array<{
        tool: string;
        result: any;
    }>;
}
```

---

## 7. 状态管理与检查点

### 7.1 LangGraph 检查点系统

Python 后端使用 `MemorySaver` 持久化执行状态：

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["tools"])
```

### 7.2 会话状态

每个用户会话通过 `thread_id` 区分：

```typescript
// WebSocket 连接
const ws = new WebSocket(`ws://localhost:8123/ws/${threadId}`);
```

---

## 8. 前端工具渲染

### 8.1 工具执行时机

当后端 LangGraph 中断并返回工具调用信息时，前端的工具 `render()` 方法被触发：

```typescript
async render(tool) {
    if (tool.client.status === 'interrupted' && tool.state === 'interrupted') {
        // 执行实际的浏览器操作
        const actionResult = await context.shortcuts.click_element_by_index(index);
        // 恢复后端执行
        tool.sendResumeData({ type: 'respond', message: JSON.stringify(actionResult) });
    }
}
```

### 8.2 工具执行结果

工具执行完成后，调用 `sendResumeData()` 恢复后端：

```typescript
interface ResumeData {
    type: 'respond' | 'reject';
    message?: string;
    error?: string;
}
```

---

## 9. API 接口参考

### 9.1 TypeScript 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/graph/assistants/search` | GET | 搜索助手列表 |
| `/v1beta/graphs/page-agent/runs` | POST | 创建运行实例 |
| `/v1beta/graphs/page-agent/runs/{run_id}` | GET | 获取运行状态 |
| `/ws/{thread_id}` | WebSocket | 实时通信 |

### 9.2 Python 后端 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/chat` | POST | 基础聊天接口 |
| `/v1beta/graphs/page-agent/runs` | POST | 创建运行实例 |
| `/v1beta/graphs/page-agent/runs/{run_id}` | GET | 获取运行状态 |
| `/ws/{thread_id}` | WebSocket | 实时通信 |

---

## 10. 总结

Page-Six Agent 的核心设计理念：

1. **前后端分离**: 前端负责 UI 和工具渲染，后端负责 Agent 编排
2. **Human-in-the-Loop**: 工具执行前中断，需前端确认
3. **快捷方式机制**: Agent 使用索引方式操作页面元素
4. **流式响应**: 通过 SSE 实时返回执行进度

这种架构使得系统既保证了 Agent 的自主性，又保留了人工干预的能力，适合需要精确控制的浏览器自动化场景。
