import json
import math

import pymupdf
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk
from app.rag.generator import generate_embedding


def extract_pdf_text(file_bytes: bytes) -> str:
    document = pymupdf.open(
        stream=file_bytes,
        filetype="pdf",
    )

    pages = []

    for page in document:
        text = page.get_text()

        if text.strip():
            pages.append(text.strip())

    document.close()

    return "\n\n".join(pages)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    if not text.strip():
        return []

    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size

        chunk = " ".join(words[start:end]).strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(words):
            break

        start = end - overlap

    return chunks


async def ingest_document(
    db: AsyncSession,
    document_id: int,
    file_bytes: bytes,
) -> int:
    text = extract_pdf_text(file_bytes)

    chunks = chunk_text(text)

    for index, chunk in enumerate(chunks):
        embedding = await generate_embedding(chunk)

        document_chunk = DocumentChunk(
            document_id=document_id,
            content=chunk,
            chunk_index=index,
            embedding=json.dumps(embedding),
        )

        db.add(document_chunk)

    await db.commit()

    return len(chunks)


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    if not first or not second:
        return 0.0

    if len(first) != len(second):
        return 0.0

    dot_product = sum(
        first_value * second_value
        for first_value, second_value in zip(first, second)
    )

    first_norm = math.sqrt(
        sum(value * value for value in first)
    )

    second_norm = math.sqrt(
        sum(value * value for value in second)
    )

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return dot_product / (first_norm * second_norm)


async def retrieve_chunks(
    db: AsyncSession,
    question: str,
    limit: int = 5,
) -> list[DocumentChunk]:
    question_embedding = await generate_embedding(question)

    result = await db.execute(
        select(DocumentChunk).where(
            DocumentChunk.embedding.is_not(None)
        )
    )

    chunks = result.scalars().all()

    scored_chunks = []

    for chunk in chunks:
        if not chunk.embedding:
            continue

        embedding = json.loads(chunk.embedding)

        score = cosine_similarity(
            question_embedding,
            embedding,
        )

        scored_chunks.append(
            (score, chunk)
        )

    scored_chunks.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return [
        chunk
        for _, chunk in scored_chunks[:limit]
    ]


async def build_context(
    db: AsyncSession,
    question: str,
    limit: int = 5,
) -> str:
    chunks = await retrieve_chunks(
        db=db,
        question=question,
        limit=limit,
    )

    return "\n\n---\n\n".join(
        chunk.content
        for chunk in chunks
    )