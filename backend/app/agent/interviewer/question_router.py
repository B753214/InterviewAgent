from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.agent.schemas.llm_output import RouterDecision
from backend.app.agent.state import InterviewState
from backend.app.llm.model_router import get_llm, log_llm_failure, log_llm_success, now_ms


def _apply_decision(
    decision,
    follow_up_count: int,
    unclear_count: int,
    current_round: int,
    max_rounds: int,
    router_source: str,
) -> dict:
    action = decision if isinstance(decision, dict) else decision.model_dump()

    if current_round >= max_rounds:
        return {
            "action": "assess",
            "follow_up_count": follow_up_count,
            "unclear_count": unclear_count,
            "router_source": router_source,
        }

    if follow_up_count >= 3:
        action["action"] = "switch_topic"

    next_unclear_count = unclear_count
    if action.get("quality") in ("unknown", "wrong"):
        next_unclear_count = unclear_count + 1
    else:
        next_unclear_count = 0

    if next_unclear_count >= 2:
        action["action"] = "switch_topic"

    result = {"action": action["action"], "router_source": router_source}

    if action["action"] == "follow_up":
        result["follow_up_count"] = follow_up_count + 1
        result["unclear_count"] = next_unclear_count
    elif action["action"] == "switch_topic":
        result["follow_up_count"] = 0
        result["unclear_count"] = next_unclear_count
    else:
        result["follow_up_count"] = follow_up_count
        result["unclear_count"] = next_unclear_count

    if action["action"] == "switch_topic" and action.get("next_topic"):
        result["current_topic"] = action["next_topic"]

    return result


async def question_router_node(state: InterviewState) -> dict:
    user_messages = [m for m in state.get("messages", []) if isinstance(m, HumanMessage)]
    if not user_messages:
        return {"action": state.get("action", "initial_question")}

    latest_answer = user_messages[-1].content
    follow_up_count = state.get("follow_up_count", 0)
    unclear_count = state.get("unclear_count", 0)
    current_round = state.get("current_round", 0)
    max_rounds = state.get("max_rounds", 8)

    llm = get_llm("question_router")
    if not llm:
        raise RuntimeError("question_router LLM is not configured")

    started_ms = now_ms()
    structured_llm = llm.with_structured_output(RouterDecision)
    try:
        decision = await structured_llm.ainvoke([
            SystemMessage(content=(
                "你是面试路由器。根据用户最新回答，决定下一步动作。\n"
                f"当前轮次: {current_round}/{max_rounds}, 追问次数: {follow_up_count}\n"
                "规则: 回答含糊→follow_up, 回答充分→switch_topic, 达到最大轮次→assess\n"
                "用户连续说不知道→switch_topic, follow_up_count>=3→switch_topic"
            )),
            HumanMessage(content=latest_answer),
        ])
        if not decision:
            raise ValueError("empty structured response")
        log_llm_success("question_router", started_ms)
        return _apply_decision(
            decision, follow_up_count, unclear_count, current_round, max_rounds, "llm"
        )
    except Exception as exc:
        log_llm_failure("question_router", exc, started_ms)
        raise
