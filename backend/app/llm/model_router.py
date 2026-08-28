import logging
import time

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
    return AGENT_MODEL_MAP.get(agent, "") or settings.DEFAULT_LLM_MODEL


def _llm_credentials() -> tuple[str, str, str] | None:
    api_key = settings.DEFAULT_LLM_API_KEY
    base_url = (settings.DEFAULT_LLM_BASE_URL or "").strip()
    model = settings.DEFAULT_LLM_MODEL
    if api_key and base_url and model:
        return api_key, base_url, model
    return None


def is_llm_available() -> bool:
    """True when DEFAULT_LLM_* credentials are fully configured."""
    return _llm_credentials() is not None


def get_llm(agent: str):
    creds = _llm_credentials()
    if not creds:
        return None
    api_key, base_url, _default_model = creds
    return init_chat_model(
        model=get_model_name(agent),
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )


def now_ms():
    return int(time.perf_counter() * 1000)


def log_llm_success(agent: str, started_ms: float | None = None) -> None:
    creds = _llm_credentials()
    base_url = creds[1] if creds else ""
    elapsed = f" elapsed_ms={int(now_ms() - started_ms)}" if started_ms else ""
    file_logger.info(
        "agent=%s model=%s status=success base_url=%s%s",
        agent,
        get_model_name(agent),
        base_url,
        elapsed,
    )


def log_llm_failure(agent: str, exc: Exception, started_ms: float | None = None) -> None:
    creds = _llm_credentials()
    base_url = creds[1] if creds else ""
    reason = f"{type(exc).__name__}: {exc}"
    elapsed = f" elapsed_ms={int(now_ms() - started_ms)}" if started_ms else ""
    console_logger.info(
        "agent=%s model=%s status=failure reason=%s%s",
        agent,
        get_model_name(agent),
        reason,
        elapsed,
    )
    file_logger.error(
        "agent=%s model=%s status=failure base_url=%s%s error=%s",
        agent,
        get_model_name(agent),
        base_url,
        elapsed,
        reason,
    )
