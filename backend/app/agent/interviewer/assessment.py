from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.agent.schemas.llm_output import AssessmentResult
from backend.app.agent.state import InterviewState
from backend.app.llm.model_router import get_llm, now_ms, log_llm_failure,log_llm_success


def _build_conversation(messages):
    return "\n".join([
            f"{'面试官' if m.type == 'ai' else '候选人'}: {m.content}"
            for m in messages
    ])


async def evaluate_conversation(llm, conversation):
    try:
        structured_llm = llm.with_structured_output(AssessmentResult)
        assessment = await structured_llm.ainvoke([
            SystemMessage(content=(
                "你是面试评估专家。请根据以下面试对话，给出结构化评估报告。\n"
                "包括: 总评分(0-100)、技术评分、沟通评分、亮点、薄弱项、建议复习知识点、\n"
                "以及每个相关知识点的 memory_updates (topic, category, performance, evidence)。"
            )),
            HumanMessage(content=conversation),
        ])
        return assessment.model_dump() if hasattr(assessment, 'model_dump') else assessment
    except Exception:
        raise ValueError("evaluate conversation failed")
        return {}

async def assessment_node(state: InterviewState):
    messages = state.get("messages", [])
    conversation = _build_conversation(messages)
    llm=get_llm("assessment")
    started_ms = now_ms()
    if llm:
        try:
            result=evaluate_conversation(llm, conversation)
            if not result:
                raise ValueError("empty structured response")
            log_llm_success("assessment", started_ms)
            return {
                "assessment": result,
                "assessment_status": "success",
                "assessment_error": "",
                "memory_updates": result.get("memory_updates", []),
                # "report_path": markdown_store.write_report(state.get("session_id", ""), result),
            }

        except Exception as exc:
            log_llm_failure("assessment", exc, started_ms)
            return {
                "assessment": None,
                "assessment_status": "failed",
                "assessment_error": f"{type(exc).__name__}: {exc}",
                "memory_updates": [],
            }

    return {
        "assessment": None,
        "assessment_status": "failed",
        "assessment_error": "LLM is not configured",
        "memory_updates": [],
    }