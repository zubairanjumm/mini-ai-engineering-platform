from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 10,
) -> list[dict[str, str]]:
    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    messages = list(
        result.scalars().all()
    )

    messages.reverse()

    return [
        {
            "role": message.role,
            "content": message.content,
        }
        for message in messages
    ]


async def build_conversation_context(
    db: AsyncSession,
    conversation_id: int,
    limit: int = 10,
) -> str:
    history = await get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        limit=limit,
    )

    if not history:
        return "No previous conversation."

    return "\n".join(
        f"{message['role']}: {message['content']}"
        for message in history
    )