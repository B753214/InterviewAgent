from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, SystemMessage

from backend.app.agent.state import InterviewState
from backend.app.llm.mock_llm import mock_interviewer_question
from backend.app.llm.model_router import get_llm, log_llm_failure, log_llm_success, now_ms
from backend.app.rag.retrieval import format_context, retrieve_material_context


def _retrieve_context(topic: str, state: InterviewState) -> list[dict]:
    material_ids = state.get("selected_material_ids", [])
    if not material_ids:
        return []

    latest_user_answer = ""
    for message in reversed(state.get("messages", [])):
        if getattr(message, "type", "") == "human":
            latest_user_answer = message.content
            break

    job = state.get("job_profile") or {}
    query = " ".join([
        topic or "",
        job.get("domain", ""),
        latest_user_answer,
    ]).strip()
    return retrieve_material_context(query, material_ids, top_k=2)


def _build_system_prompt(action: str, topic: str, context: str, weakness_memory: list[dict]) -> str:
    base = "你是一位专业的面试官。请根据以下信息生成面试问题。用中文提问，保持自然、专业。"
    if action == "initial_question":
        base += f"\n这是一场面试的开场。请结合以下主题提问: {topic}"
    elif action == "follow_up":
        base += f"\n请针对候选人上一轮的回答进行深入追问。当前话题: {topic}"
    elif action == "switch_topic":
        base += f"\n请平滑切换到新话题并提问。新话题: {topic}"
    if context:
        base += f"\n\n参考资料:\n{context}"
    if weakness_memory:
        base += "\n\n历史薄弱点画像:\n"
        for memory in weakness_memory[:5]:
            base += (
                f"- {memory.get('topic', '')}: 掌握度 {memory.get('mastery_score', 0):.2f}, "
                f"薄弱次数 {memory.get('weakness_count', 0)}\n"
            )
        base += "请优先围绕目标岗位相关且历史掌握度较低的话题提问，避免生硬重复。"
    base += "\n\n只输出问题本身，不要加任何说明文字。"
    return base


def _build_prompt_messages(
    action: str,
    topic: str,
    context: str,
    messages: list,
    weakness_memory: list[dict],
) -> list:
    system_prompt = _build_system_prompt(action, topic, context, weakness_memory)
    prompt_messages = [SystemMessage(content=system_prompt)]
    for message in messages[-6:]:
        prompt_messages.append(message)
    return prompt_messages


def prepare_interviewer_stream(state: InterviewState) -> tuple[list, list[dict]]:
    action = state.get("action", "initial_question")
    current_topic = state.get("current_topic", "")
    messages = list(state.get("messages", []))
    weakness_memory = state.get("weakness_memory", [])
    retrieved_chunks = _retrieve_context(current_topic, state)
    context = format_context(retrieved_chunks)
    prompt_messages = _build_prompt_messages(
        action, current_topic, context, messages, weakness_memory
    )
    return prompt_messages, retrieved_chunks


async def stream_interviewer_tokens(state: InterviewState) -> AsyncIterator[str]:
    action = state.get("action", "initial_question")
    current_topic = state.get("current_topic", "")
    llm = get_llm("interviewer")
    if not llm:
        text = mock_interviewer_question(action, current_topic)
        for i in range(0, len(text), 3):
            yield text[i : i + 3]
        return

    prompt_messages, _ = prepare_interviewer_stream(state)
    started_ms = now_ms()
    try:
        async for chunk in llm.astream(prompt_messages):
            token = getattr(chunk, "content", None) or ""
            if isinstance(token, list):
                token = "".join(
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in token
                )
            if token:
                yield token
        log_llm_success("interviewer", started_ms)
    except Exception as exc:
        log_llm_failure("interviewer", exc, started_ms)
        text = mock_interviewer_question(action, current_topic)
        for i in range(0, len(text), 3):
            yield text[i : i + 3]


async def interviewer_node(state: InterviewState) -> dict:
    action = state.get("action", "initial_question")
    current_topic = state.get("current_topic", "")
    _, retrieved_chunks = prepare_interviewer_stream(state)

    llm = get_llm("interviewer")
    if not llm:
        question_text = mock_interviewer_question(action, current_topic)
        return {
            "messages": [AIMessage(content=question_text)],
            "current_round": state.get("current_round", 0) + 1,
            "retrieved_context": retrieved_chunks,
        }

    prompt_messages, retrieved_chunks = prepare_interviewer_stream(state)
    started_ms = now_ms()
    try:
        response = await llm.ainvoke(prompt_messages)
        question_text = response.content if response else ""
        if not question_text:
            raise ValueError("empty response content")
        log_llm_success("interviewer", started_ms)
        return {
            "messages": [AIMessage(content=question_text)],
            "current_round": state.get("current_round", 0) + 1,
            "retrieved_context": retrieved_chunks,
        }
    except Exception as exc:
        log_llm_failure("interviewer", exc, started_ms)
        question_text = mock_interviewer_question(action, current_topic)
        return {
            "messages": [AIMessage(content=question_text)],
            "current_round": state.get("current_round", 0) + 1,
            "retrieved_context": retrieved_chunks,
        }
