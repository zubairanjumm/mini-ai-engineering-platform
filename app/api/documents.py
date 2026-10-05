from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Document


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


@router.post("/")
async def upload_document(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    document = Document(
        user_id=user_id,
        filename=file.filename or "unknown",
        content_type=file.content_type or "application/octet-stream",
    )

    db.add(document)

    await db.commit()
    await db.refresh(document)

    return {
        "id": document.id,
        "user_id": document.user_id,
        "filename": document.filename,
        "content_type": document.content_type,
        "message": "Document registered successfully.",
    }


@router.get("/user/{user_id}")
async def get_user_documents(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == user_id)
        .order_by(Document.created_at.desc())
    )

    documents = result.scalars().all()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "content_type": document.content_type,
            "created_at": document.created_at,
        }
        for document in documents
    ]