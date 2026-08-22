import time
import logging

from langchain.chat_models import init_chat_model

from backend.app.config import settings
file_logger = logging.getLogger("model_calls.file")
console_logger = logging.getLogger("model_calls.console")

AGENT_MODEL_MAP = {
    "resume_analyzer": settings.RESUME_ANALYZER_MODEL,
    "job_analyzer": settings.JOB_ANALYZER_MODEL,
    "question_router": settings.QUESTION_ROUTER_MODEL,
    "interviewer": settings.INTERVIEWER_MODEL,
    "assessment": settings.ASSESSMENT_MODEL,
    "pdf_vision": settings.PDF_VISION_AGENT_MODEL,
}
def get_model_name(agent: str) -> str:
    """Return the model name for a given agent, falling back to default."""
    return AGENT_MODEL_MAP.get(agent, "") or settings.DEFAULT_LLM_MODEL
def get_llm(agent: str):
    """按 agent 返回 chat model；未配置 API Key 时返回 None。"""
    if not (settings.DEFAULT_LLM_API_KEY and settings.DEFAULT_LLM_BASE_URL and settings.DEFAULT_LLM_MODEL):
        return None
    return init_chat_model(
        model=get_model_name(agent),
        api_key=settings.DEFAULT_LLM_API_KEY,
        base_url=settings.DEFAULT_LLM_BASE_URL,
        temperature=0.7,
    )


def now_ms():
    return int(time.perf_counter() * 1000)

def log_llm_success(agent: str, started_ms: float | None = None)->None:
    file_logger.info(
        "agent=%s model=%s status=success base_url=%s%s",
        agent,
    )
def log_llm_failure(agent: str, exc: Exception, started_ms: float | None = None)->None:
    reason = f"{type(exc).__name__}: {exc}"
    console_logger.info(
        "agent=%s model=%s status=failure reason=%s%s",
        agent,
        reason,
    )
    file_logger.error(
        "agent=%s model=%s status=failure base_url=%s%s error=%s",
        agent,
        reason,
    )
