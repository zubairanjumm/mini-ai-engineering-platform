from typing import TypedDict


class GraphState(TypedDict):
    question: str
    conversation_id: int
    context: str
    history: str
    answer: str