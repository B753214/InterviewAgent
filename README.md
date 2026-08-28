# InterviewAgent

基于 FastAPI + LangGraph + Next.js 的智能模拟面试系统。

当前能力：多轮面试（真流式出题）、简历/岗位 LLM 画像、Markdown/PDF 资料 RAG、长期记忆与 rebuild 重评、无 Key 时 Mock 降级。完整计划见 [`plan/`](./plan/)。

## 快速启动

### 1. 环境准备

```bash
cd InterviewAgent
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入 DEFAULT_LLM_API_KEY 等
```

### 3. 启动服务

在项目根目录执行：

```bash
python main.py
```

或：

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API：http://localhost:8000
- Swagger：http://localhost:8000/docs

## 当前接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务信息 |
| GET/POST | `/interviews` | 列表 / 创建面试 |
| GET | `/interviews/{id}` | 会话详情 |
| GET | `/interviews/{id}/report` | 评估报告 |
| POST | `/interviews/{id}/answer` | 提交回答 |
| POST | `/interviews/{id}/answer/stream` | SSE 真流式出题 |
| POST | `/interviews/{id}/finish` | 提前结束并评估 |
| POST | `/interviews/{id}/assess` | 重新评估 |
| GET/POST | `/resumes` | 简历画像 |
| GET | `/resumes/{id}` | 简历详情 |
| GET/POST | `/jobs` | 岗位画像 |
| GET/POST | `/materials` | 面试资料（Markdown） |
| POST | `/materials/upload` | 上传 PDF 资料 |
| GET | `/materials/{id}` | 资料详情 |
| GET | `/memories` | 知识点记忆列表 |
| POST | `/memories/rebuild` | 重评历史面试并重建记忆 |

> 未配置 `DEFAULT_LLM_API_KEY` 时，面试链路会自动走 Mock LLM，仍可本地演示。

## 前端（M6）

```bash
cd apps/web
cp .env.local.example .env.local   # 默认 http://localhost:8000
npm install
npm run dev
```

- 前端：http://localhost:3000
- 需先启动后端 `python main.py`

页面：首页、我的档案（含 PDF 上传）、模拟面试（流式）、面试历史、能力图谱。

## 项目结构

```text
InterviewAgent/
  main.py                 # FastAPI 入口
  apps/web/               # Next.js 前端
  requirements.txt
  .env.example
  plan/                   # 差距分析与补齐计划
  backend/app/
    config.py             # 环境变量
    database.py           # 异步 SQLAlchemy
    api/                  # 路由
    agent/                # LangGraph 节点与 prompts
    services/             # 业务逻辑（含 pdf / memory / profile_analyzer）
    rag/                  # chunk / embed / milvus / retrieval
    llm/                  # model_router + mock_llm
    models/               # ORM
```

## 配置说明

主要变量见 [`.env.example`](./.env.example)，与 `backend/app/config.py` 对应：

| 变量 | 含义 | 默认 |
|------|------|------|
| `DATABASE_URL` | 异步数据库 URL | `sqlite+aiosqlite:///./interview.db` |
| `DEFAULT_LLM_API_KEY` | LLM API Key（可空，走 Mock） | 空 |
| `DEFAULT_LLM_BASE_URL` | LLM Base URL | `https://api.deepseek.com/v1` |
| `DEFAULT_LLM_MODEL` | 默认模型名 | `deepseek-chat` |
| `CORS_ORIGINS` | 跨域来源 | localhost:3000 等 |
| `MILVUS_URI` | Milvus 地址 | `http://localhost:19530` |

## 实施进度

详见 [`plan/roadmap.md`](./plan/roadmap.md) 与 [`plan/README.md`](./plan/README.md)。

- M0–M6 主链路 ✅
- 真流式 SSE / Mock LLM / PDF 文本层 / rebuild 重评 ✅
- 二期可选：PDF vision、`/health`、markdown 落盘
