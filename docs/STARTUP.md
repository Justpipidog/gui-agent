# Page-Six Agent 服务启动指南

本文档提供 Page-Six Agent 项目的所有服务启动操作说明，包括环境配置、依赖安装、服务启动和故障排查。

## 1. 环境要求

### 1.1 必需软件

| 软件 | 版本要求 | 用途 |
|------|----------|------|
| **Node.js** | >= 18.0.0 | 前端构建 |
| **PNPM** | >= 8.0.0 | 包管理器 (推荐) |
| **Bun** | >= 1.0.0 | TypeScript 后端运行时 |
| **Python** | >= 3.9 | Python 后端运行时 |
| **UV** | latest | Python 包管理器 (推荐) |

### 1.2 可选软件

| 软件 | 用途 |
|------|------|
| **Git** | 版本控制 |
| **VS Code** | 推荐编辑器 |

---

## 2. 项目结构

```
page-agent-langgraph/
├── docs/                      # 文档目录
├── python-backend/            # Python 后端 (FastAPI)
│   ├── backend/
│   │   ├── main.py            # 主应用入口
│   │   └── utils.py           # 工具函数
│   ├── .env.example           # 环境变量模板
│   ├── pyproject.toml         # Python 依赖配置
│   └── run_server.py          # 启动脚本
├── page-six-agent/            # TypeScript Monorepo
│   ├── packages/
│   │   ├── page-agent-server/ # LangGraph 后端 (Bun + Hono)
│   │   │   └── src/
│   │   │       ├── graph/        # LangGraph 工作流定义
│   │   │       ├── prompt/       # 中文系统提示词
│   │   │       ├── tools/        # 工具定义
│   │   │       └── frontend/     # PageAgentContext, 快捷方式
│   │   └── solid-ui/             # SolidJS 前端
│   │       └── src/
│   │           └── components/
│   │               ├── chat/         # 聊天 UI
│   │               └── gateway/      # 网关管理 UI
│   ├── package.json           # 根目录依赖配置
│   └── pnpm-workspace.yaml    # PNPM 工作区配置
└── package.json               # 根目录依赖
```

---

## 3. 环境配置

### 3.1 克隆项目

```bash
# 克隆仓库
git clone <repository-url>
cd page-agent-langgraph
```

### 3.2 安装 Node.js 依赖

在项目根目录安装依赖：

```bash
# 使用 pnpm 安装 (推荐)
pnpm install

# 或使用 npm
npm install
```

### 3.3 配置 Python 后端 (可选)

如果需要使用 Python 后端：

```bash
cd python-backend

# 使用 UV 安装依赖 (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt

# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置 API 密钥
notepad .env
```

`.env` 文件配置示例：

```env
# 智谱 AI 配置
LLM_MODEL_NAME=qwen-plus
GLM_API_KEY=your_api_key_here

# 或 OpenAI 配置
# LLM_MODEL_NAME=gpt-4
# OPENAI_API_KEY=your_api_key_here
```

---

## 4. 服务启动

### 4.1 启动所有服务 (推荐)

在 PowerShell 中，可以使用脚本来启动所有服务：

```powershell
# 启动 TypeScript 后端
cd "D:\code\page-agent-langgraph\page-six-agent\packages\page-agent-server"
bun run dev

# 启动 Python 后端 (新终端)
cd "D:\code\page-agent-langgraph\python-backend"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 启动前端 (新终端)
cd "D:\code\page-agent-langgraph\page-six-agent\packages\solid-ui"
pnpm dev
```

### 4.2 单独启动各服务

#### 4.2.1 TypeScript 后端 (Bun + Hono)

```bash
cd page-six-agent/packages/page-agent-server
bun run dev
```

- **端口**: 8123
- **地址**: http://localhost:8123
- **特点**: 使用 Bun 运行时，@langgraph-js 生态

#### 4.2.2 Python 后端 (FastAPI)

```bash
cd python-backend

# 方式一: 直接运行
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 方式二: 使用启动脚本
python run_server.py
```

- **端口**: 8000
- **地址**: http://localhost:8000
- **特点**: Python 实现，兼容 LangGraph JS SDK

#### 4.2.3 SolidJS 前端

```bash
cd page-six-agent/packages/solid-ui
pnpm dev
```

- **端口**: 5173 (如被占用则自动使用其他端口)
- **地址**: http://localhost:5173
- **特点**: Vite 开发服务器，支持热更新

---

## 5. 切换后端

前端默认连接 TypeScript 后端。如需切换到 Python 后端，修改代理配置：

### 5.1 临时切换 (开发时)

在 `vite.config.ts` 中修改代理 target：

```typescript
// TypeScript 后端
'/api/langgraph': {
    target: 'http://localhost:8123',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/langgraph/, ''),
},

// 或切换到 Python 后端
'/api/langgraph': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api\/langgraph/, ''),
},
```

### 5.2 使用环境变量

创建 `.env.local` 文件：

```env
VITE_LANGGRAPH_API_URL=http://localhost:8000
```

---

## 6. 验证服务状态

### 6.1 检查端口占用

```powershell
# 检查所有相关端口
netstat -ano | findstr ":5173\|:8000\|:8123"
```

### 6.2 测试 API 接口

```bash
# 测试 TypeScript 后端
curl http://localhost:8123/graph/assistants/search

# 测试 Python 后端
curl http://localhost:8000/docs
```

### 6.3 访问前端页面

打开浏览器访问：

- 前端页面: http://localhost:5173 (或终端显示的实际端口)
- API 文档 (Python): http://localhost:8000/docs

---

## 7. 常见问题

### 7.1 端口被占用

**问题**: 启动时提示端口已被占用

**解决方案**:

```powershell
# 查找占用端口的进程
netstat -ano | findstr ":5173"

# 终止进程 (替换 PID 为实际进程ID)
taskkill /PID <PID> /F
```

### 7.2 Bun 命令未找到

**问题**: `bun : 无法将"bun"项识别为 cmdlet、函数、脚本文件或可运行程序的名称`

**解决方案**:

```powershell
# 使用完整路径
& "C:\Users\<用户名>\.bun\bin\bun.exe" run dev

# 或添加到 PATH
$env:PATH += ";$env:BUN_INSTALL\bin"
```

### 7.3 Python 依赖安装失败

**问题**: `uv sync` 失败或缺少依赖

**解决方案**:

```bash
# 升级 uv
uv pip install --upgrade

# 清理缓存后重试
uv cache clean
uv sync --refresh
```

### 7.4 前端代理不生效

**问题**: 请求后端 API 返回 404 或跨域错误

**解决方案**:

1. 重启前端开发服务器
2. 检查 vite.config.ts 代理配置
3. 确认后端服务正在运行

### 7.5 WebSocket 连接失败

**问题**: 工具执行时 WebSocket 连接失败

**解决方案**:

```bash
# 检查 WebSocket 端口
# TypeScript 后端: ws://localhost:8123/ws/{thread_id}
# Python 后端: ws://localhost:8000/ws/{thread_id}

# 确保没有代理或防火墙阻止连接
```

---

## 8. 生产部署

### 8.1 构建前端

```bash
cd page-six-agent/packages/solid-ui
pnpm build
```

构建产物位于 `dist/` 目录。

### 8.2 部署后端

#### TypeScript 后端 (生产)

```bash
cd page-six-agent/packages/page-agent-server

# 使用 Bun 打包
bun build ./src/index.ts --outdir ./dist --target bun

# 或使用 Node.js
bun build ./src/index.ts --outdir ./dist --target node
```

#### Python 后端 (生产)

```bash
cd python-backend

# 使用 gunicorn 替代 uvicorn (推荐)
pip install gunicorn
gunicorn backend.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 8.3 Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态资源
    location / {
        root /path/to/solid-ui/dist;
        try_files $uri $uri/ /index.html;
    }

    # TypeScript 后端代理
    location /api/langgraph/ {
        proxy_pass http://localhost:8123;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket 支持
    location /ws/ {
        proxy_pass http://localhost:8123;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_read_timeout 86400;
    }
}
```

---

## 9. 开发技巧

### 9.1 使用 Claude Code

项目已配置 CLAUDE.md，可以直接向 Claude Code 询问：

```
"前端是怎么发送消息到后端的？"
"如何添加新的快捷方式？"
"Human-in-the-Loop 是怎么工作的？"
```

### 9.2 代码热重载

- **TypeScript 后端**: Bun 自动热重载
- **Python 后端**: uvicorn --reload
- **前端**: Vite 热模块替换 (HMR)

### 9.3 调试工具

浏览器开发者工具:
- **Network**: 查看 API 请求和响应
- **Console**: 查看前端日志
- **Sources**: 设置断点调试

---

## 10. 联系与支持

如有问题，请：

1. 查看本文档的故障排查部分
2. 查看项目 Issues
3. 向项目维护者提问
