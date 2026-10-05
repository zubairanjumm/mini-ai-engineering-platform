from sqlalchemy.ext.asyncio import AsyncSession

from app.langgraph.workflow import run_chat_workflow


async def execute_workflow(
    question: str,
    conversation_id: int,
    db: AsyncSession,
) -> str:
    return await run_chat_workflow(
        question=question,
        conversation_id=conversation_id,
        db=db,
    )