from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Document, User
from app.rag.retriever import ingest_document


router = APIRouter(
    prefix="/api/documents",
    tags=["documents"],
)


@router.post("/")
async def upload_document(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(
        select(User).where(User.id == user_id)
    )

    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty",
        )

    document = Document(
        user_id=user_id,
        filename=file.filename or "document.pdf",
        content_type=file.content_type,
    )

    db.add(document)

    await db.flush()

    chunk_count = await ingest_document(
        db=db,
        document_id=document.id,
        file_bytes=file_bytes,
    )

    return {
        "id": document.id,
        "filename": document.filename,
        "content_type": document.content_type,
        "chunks_created": chunk_count,
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