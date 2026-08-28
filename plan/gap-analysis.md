# 差距分析：InterviewAgent vs interview-agent

> 更新：2026-08-28。M0–M6 及主要体验增强已对齐；下文标注**仍可选**的二期差距。

## 对比结论

| 维度 | InterviewAgent（本仓库） | interview-agent（参考） |
|------|--------------------------|-------------------------|
| 形态 | FastAPI + LangGraph 五节点状态机 | 可跑通的多画像模拟面试系统 |
| Agent | 五节点图 + 多角色 LLM 路由 + Mock 降级 | 同左 |
| 数据 | SQLite + Milvus；`interview_sessions` 宽表 | JSON / Supabase + Markdown 产物 |
| RAG | Milvus + SQLite 正文；Markdown + **PDF 文本层** | pgvector / 内存退化；PDF + vision + queue |
| 记忆 | SQLite；**rebuild 重评** | 同结构；rebuild 重评 |
| 流式 | **interviewer 真流式** `astream` | 整句切块伪流式 |
| 前端 | Next.js `apps/web` 已接入 | Next.js |
| 工程 | README、`.env.example`、`requirements.txt` | 完整 |

```mermaid
flowchart LR
  subgraph ref [interview-agent]
    Resume[简历画像]
    Job[岗位画像]
    Mat[资料RAG]
    Graph[五节点状态机]
    Mem[长期记忆]
    Web[Next前端]
  end
  subgraph yours [InterviewAgent 现状]
    YResume[简历/岗位 ✅]
    YMat[RAG+PDF文本 ✅]
    YGraph[五节点+真流式 ✅]
    YMem[记忆+重评rebuild ✅]
    YWeb[Next 前端 ✅]
  end
  ref -.->|"二期可选"| Vision[PDF vision/queue]
  ref -.->|"二期可选"| Health[/health]
```

---

## 已对齐

| 能力 | 本仓库实现 |
|------|------------|
| 真实 LLM 出题/评分 | `interviewer` / `assessment` + `model_router` |
| Mock LLM 降级 | `llm/mock_llm.py`；router / interviewer / assessment |
| 会话持久化 | `interview_sessions` + `interview_service` |
| 多轮对话 | `POST /answer` + **`/answer/stream` 真流式** |
| 追问/切题路由 | `question_router` |
| 结构化评估 | `AssessmentResult` + `/report` |
| 简历/岗位画像 | `/resumes`、`/jobs` + `profile_analyzer` |
| 资料 RAG | `/materials` + Milvus + `retrieval` |
| PDF 上传（文本层） | `POST /materials/upload` + `pdf_service` + 前端 Profile |
| 长期记忆 | `memory_updater` + `/memories` |
| rebuild 完整版 | 对 ended 场次 `_reassess_interview_record` 后再 apply |
| 前端全链路 | profile / interview / history / skills |

---

## 仍可选的差距（二期）

| 缺口 | 参考 | 本仓库 | 优先级 |
|------|------|--------|--------|
| PDF vision / 异步队列 | `vision_service` + `material_queue` | 仅 pypdf 文本层；扫描件会 failed | P2 |
| `GET /health` | 有 | 无 | P2 |
| markdown 落盘 | `markdown_store` | 无 | P2 |
| `/materials/reprocess` | 有 | 无 | P2 |
| 多用户 / 认证 | 无（同） | 无 | 可后置 |
| 自动化测试 | 几乎无 | 几乎无 | P2 |

---

## Agent 架构（已对齐）

```text
initializer → question_router → interviewer | assessment → memory_updater → END
```

流式路径：`stream_submit_answer` = initializer + router →（assess 或 interviewer.astream）

---

## 本仓库文件状态

| 文件/目录 | 状态 |
|-----------|------|
| `main.py` | ✅ 注册 interviews / resumes / jobs / materials / memories |
| `backend/app/agent/interviewer/graph.py` | ✅ 五节点主图 |
| `backend/app/llm/mock_llm.py` | ✅ Mock 降级 |
| `backend/app/rag/*` | ✅ chunk / embed / milvus / retrieval |
| `backend/app/services/pdf_service.py` | ✅ PDF 文本抽取 |
| `backend/app/services/memory_service.py` | ✅ 持久化 + rebuild 重评 |
| `backend/app/services/profile_analyzer.py` | ✅ resume/job LLM + fallback |
| `apps/web/` | ✅ Next.js 前端 |
| `backend/app/agent/evaluator/graph.py` | ✅ 独立评估图（保留） |

详细任务状态见 [roadmap.md](./roadmap.md)。  
五节点流程见 [nodes-spec.md](./nodes-spec.md)。
