from langgraph.types import interrupt


def get_user_input() -> str:
    input=interrupt("请输入您的回答：")
