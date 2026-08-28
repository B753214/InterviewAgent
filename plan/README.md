# InterviewAgent 实施计划

对照更完整的参考实现 [`../interview-agent`](../../interview-agent)（同级目录），梳理本仓库缺口与分阶段落地计划。

| 文档 | 说明 |
|------|------|
| [gap-analysis.md](./gap-analysis.md) | 现状 vs 参考：缺什么 |
| [roadmap.md](./roadmap.md) | M0–M6 详细补齐计划 + **当前进度与收尾** |
| [nodes-spec.md](./nodes-spec.md) | 五节点流程、职责与实现清单 |

## 当前进度（2026-08-28）

```text
M0 ██████████ 100%  工程基建
M1 ██████████ 100%  多轮面试 + finish/assess + SQLite 持久化
M2 ██████████ 100%  五节点图 + HTTP 驱动 + 画像注入
M3 ██████████ 100%  ORM + service + /resumes /jobs + LLM 解析（fallback）
M4 ██████████ 100%  Milvus + DashScope embedding + retrieval + /materials + PDF 文本层
M5 ██████████ 100%  knowledge_memories + /memories + rebuild 重评
M6 ██████████ 100%  Next.js 前端 + 真流式 SSE + Mock LLM
```

**一句话**：对标参考的主链路与 P1 体验项已完成；浏览器可完成「建档 → 开面 → 报告 → 能力图谱」全链路。

## 已落地的 API

### `/interviews`

| 方法 | 路径 | 状态 |
|------|------|------|
| GET | `/interviews` | 列表 |
| POST | `/interviews` | 创建 + 第一题 |
| GET | `/interviews/{id}` | 详情 |
| GET | `/interviews/{id}/report` | 报告 |
| POST | `/interviews/{id}/answer` | 提交回答 |
| POST | `/interviews/{id}/answer/stream` | **真流式** SSE（interviewer `astream`） |
| POST | `/interviews/{id}/finish` | 提前结束 |
| POST | `/interviews/{id}/assess` | 重新评估 |

### `/resumes` / `/jobs`

| 方法 | 路径 | 状态 |
|------|------|------|
| POST | `/resumes`、`/jobs` | 创建画像（LLM + 关键词 fallback） |
| GET | `/resumes`、`/jobs` | 列表 |
| GET | `/resumes/{id}`、`/jobs/{id}` | 详情 |

### `/materials`

| 方法 | 路径 | 状态 |
|------|------|------|
| POST | `/materials` | 创建 Markdown 资料 + 切块向量化 |
| POST | `/materials/upload` | **上传 PDF**（pypdf 文本层 → 索引） |
| GET | `/materials` | 列表 |
| GET | `/materials/{id}` | 详情 |

### `/memories`

| 方法 | 路径 | 状态 |
|------|------|------|
| GET | `/memories` | 知识点记忆列表 |
| POST | `/memories/rebuild` | **完整版**：对 ended 场次重评后再重建记忆 |

## 前端（`apps/web`）

| 页面 | 路径 | 状态 |
|------|------|------|
| 首页 | `/` | ✅ |
| 我的档案 | `/profile` | ✅ 简历 / 岗位 / Markdown + **PDF 上传** |
| 模拟面试 | `/interview` | ✅ 真流式 SSE + fallback |
| 面试历史 | `/history` | ✅ |
| 能力图谱 | `/skills` | ✅ 记忆列表 + 从历史重建（重评） |

启动：`cd apps/web && npm run dev` → http://localhost:3000（需后端 http://localhost:8000）

## 收尾状态（2026-08-28）

| 项 | 状态 |
|----|------|
| M0–M6 主链路 | ✅ 完成 |
| 真流式 SSE | ✅ |
| Mock LLM | ✅ `llm/mock_llm.py` |
| PDF 文本层上传 | ✅（无 vision / 异步队列） |
| rebuild 重评 | ✅ |
| 工程 git 提交 | 前端已提交；后端增强待收尾提交 |

## 可选后续（非阻塞 / 二期）

| # | 任务 | 说明 |
|---|------|------|
| 1 | PDF vision + 异步队列 | 扫描件识别、`/queue/status`、`/reprocess` |
| 2 | `GET /health` | ~~探活~~ **已完成** |
| 3 | markdown 落盘 | 简历/报告写 `.md` 产物 |
| 4 | 多用户 / 认证 | 两边均可后置 |
| 5 | 自动化测试 | 冒烟 / API 测试 |

详见 [roadmap.md § 可选后续](./roadmap.md#可选后续)。

## 路径约定

- **本仓库**：`d:\python\InterviewAgent`
- **参考**：`d:\python\interview-agent`
