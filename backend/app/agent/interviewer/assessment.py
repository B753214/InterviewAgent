import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agent.schemas.llm_output import AssessmentResult
from backend.app.agent.state import InterviewState
from backend.app.llm.mock_llm import mock_assessment
from backend.app.llm.model_router import get_llm, log_llm_failure, log_llm_success, now_ms


def _build_conversation(messages) -> str:
    return "\n".join([
        f"{'面试官' if m.type == 'ai' else '候选人'}: {m.content}"
        for m in messages
    ])


async def _invoke_json_llm(llm, prompt: list):
    json_llm = llm.bind(response_format={"type": "json_object"})
    return await json_llm.ainvoke(prompt)


def _parse_json_object(content: str) -> dict:
    text = content.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start:end + 1]
    return json.loads(text)


async def _assess_with_json_prompt(llm, conversation: str) -> dict:
    prompt = [
        SystemMessage(content=(
            "你是面试评估专家。必须只输出一个合法 JSON 对象。\n"
            "字段: total_score, tech_score, communication_score, highlights, weaknesses, "
            "suggested_review, memory_updates。"
        )),
        HumanMessage(content=conversation),
    ]
    response = await _invoke_json_llm(llm, prompt)
    content = response.content if response else ""
    parsed = _parse_json_object(content)
    return AssessmentResult.model_validate(parsed).model_dump()


async def evaluate_conversation(llm, conversation: str) -> dict:
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
        return assessment.model_dump() if hasattr(assessment, "model_dump") else assessment
    except Exception:
        return await _assess_with_json_prompt(llm, conversation)


async def assessment_node(state: InterviewState) -> dict:
    messages = state.get("messages", [])
    conversation = _build_conversation(messages)

    llm = get_llm("assessment")
    if not llm:
        result = mock_assessment()
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": "",
            "memory_updates": result.get("memory_updates", []),
            "report_path": "",
        }

    started_ms = now_ms()
    try:
        result = await evaluate_conversation(llm, conversation)
        if not result:
            raise ValueError("empty structured response")
        log_llm_success("assessment", started_ms)
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": "",
            "memory_updates": result.get("memory_updates", []),
            "report_path": "",
        }
    except Exception as exc:
        log_llm_failure("assessment", exc, started_ms)
        result = mock_assessment()
        return {
            "assessment": result,
            "assessment_status": "success",
            "assessment_error": f"fallback_mock: {type(exc).__name__}: {exc}",
            "memory_updates": result.get("memory_updates", []),
            "report_path": "",
        }
