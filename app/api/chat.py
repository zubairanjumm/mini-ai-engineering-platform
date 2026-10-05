from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Conversation, Message, User
from app.langgraph.workflow import run_chat_workflow


router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)


class ConversationRequest(BaseModel):
    user_id: int


class MessageRequest(BaseModel):
    conversation_id: int
    content: str


@router.post("/conversations")
async def create_conversation(
    request: ConversationRequest,
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(
        select(User).where(User.id == request.user_id)
    )

    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    conversation = Conversation(
        user_id=request.user_id,
    )

    db.add(conversation)

    await db.commit()
    await db.refresh(conversation)

    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "created_at": conversation.created_at,
    }


@router.get("/conversations/user/{user_id}")
async def get_user_conversations(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
    )

    conversations = result.scalars().all()

    return [
        {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "created_at": conversation.created_at,
        }
        for conversation in conversations
    ]


@router.post("/messages")
async def send_message(
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    conversation_result = await db.execute(
        select(Conversation).where(
            Conversation.id == request.conversation_id
        )
    )

    conversation = conversation_result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    content = request.content.strip()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty",
        )

    user_message = Message(
        conversation_id=conversation.id,
        role="user",
        content=content,
    )

    db.add(user_message)
    await db.commit()

    answer = await run_chat_workflow(
        question=content,
        conversation_id=conversation.id,
        db=db,
    )

    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
    )

    db.add(assistant_message)

    await db.commit()
    await db.refresh(assistant_message)

    return {
        "conversation_id": conversation.id,
        "question": content,
        "answer": answer,
        "message_id": assistant_message.id,
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    conversation_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id
        )
    )

    conversation = conversation_result.scalar_one_or_none()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )

    result = await db.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id
        )
        .order_by(Message.created_at.asc())
    )

    messages = result.scalars().all()

    return [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at,
        }
        for message in messages
    ]