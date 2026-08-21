from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from backend.app.database import settings


class LLMClient:
    def __init__(self):
        self.client = init_chat_model(
            model=settings.DEEPSEEK_MODEL,
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            temperature=1
        )
    async def generate(self, prompts: str):
        messages=[HumanMessage(content=p) for p in prompts]
        return await self.client.generate(messages)

_llm_client = None

def get_llm_client():
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client

