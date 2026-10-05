from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.memory import build_conversation_context
from app.rag.generator import generate_answer
from app.rag.retriever import build_context


class ChatState(TypedDict):
    question: str
    conversation_id: int
    history: str
    context: str
    answer: str


async def retrieve_context(
    state: ChatState,
    db: AsyncSession,
) -> ChatState:
    context = await build_context(
        db=db,
        question=state["question"],
        limit=5,
    )

    return {
        **state,
        "context": context,
    }


async def retrieve_memory(
    state: ChatState,
    db: AsyncSession,
) -> ChatState:
    history = await build_conversation_context(
        db=db,
        conversation_id=state["conversation_id"],
        limit=10,
    )

    return {
        **state,
        "history": history,
    }


async def generate_response(
    state: ChatState,
) -> ChatState:
    prompt_context = f"""
DOCUMENT CONTEXT:
{state["context"]}

CONVERSATION HISTORY:
{state["history"]}
"""

    answer = await generate_answer(
        question=state["question"],
        context=prompt_context,
    )

    return {
        **state,
        "answer": answer,
    }


def build_graph(
    db: AsyncSession,
):
    async def retrieve_context_node(
        state: ChatState,
    ) -> ChatState:
        return await retrieve_context(
            state=state,
            db=db,
        )

    async def retrieve_memory_node(
        state: ChatState,
    ) -> ChatState:
        return await retrieve_memory(
            state=state,
            db=db,
        )

    graph = StateGraph(ChatState)

    graph.add_node(
        "retrieve_context",
        retrieve_context_node,
    )

    graph.add_node(
        "retrieve_memory",
        retrieve_memory_node,
    )

    graph.add_node(
        "generate_response",
        generate_response,
    )

    graph.add_edge(
        START,
        "retrieve_context",
    )

    graph.add_edge(
        "retrieve_context",
        "retrieve_memory",
    )

    graph.add_edge(
        "retrieve_memory",
        "generate_response",
    )

    graph.add_edge(
        "generate_response",
        END,
    )

    return graph.compile()


async def run_chat_workflow(
    question: str,
    conversation_id: int,
    db: AsyncSession,
) -> str:
    graph = build_graph(db)

    initial_state: ChatState = {
        "question": question,
        "conversation_id": conversation_id,
        "history": "",
        "context": "",
        "answer": "",
    }

    result = await graph.ainvoke(initial_state)

    return result["answer"]