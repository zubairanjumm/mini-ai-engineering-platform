import json
import math

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DocumentChunk
from app.documents.chunker import chunk_text
from app.documents.embeddings import create_embeddings
from app.documents.loader import load_pdf
from app.rag.generator import generate_embedding


def cosine_similarity(
    first: list[float],
    second: list[float],
) -> float:
    if not first or not second:
        return 0.0

    if len(first) != len(second):
        return 0.0

    dot_product = sum(
        a * b
        for a, b in zip(first, second)
    )

    first_norm = math.sqrt(
        sum(value * value for value in first)
    )

    second_norm = math.sqrt(
        sum(value * value for value in second)
    )

    if first_norm == 0 or second_norm == 0:
        return 0.0

    return dot_product / (
        first_norm * second_norm
    )


async def ingest_document(
    db: AsyncSession,
    document_id: int,
    file_bytes: bytes,
) -> int:
    text = load_pdf(file_bytes)

    chunks = chunk_text(text)

    if not chunks:
        return 0

    embeddings = await create_embeddings(chunks)

    for index, (
        chunk,
        embedding,
    ) in enumerate(
        zip(chunks, embeddings)
    ):
        db.add(
            DocumentChunk(
                document_id=document_id,
                content=chunk,
                chunk_index=index,
                embedding=json.dumps(
                    embedding
                ),
            )
        )

    await db.commit()

    return len(chunks)


async def retrieve_chunks(
    db: AsyncSession,
    question: str,
    limit: int = 5,
) -> list[DocumentChunk]:
    question_embedding = await generate_embedding(
        question
    )

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

        embedding = json.loads(
            chunk.embedding
        )

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

    if not chunks:
        return "No relevant document context was found."

    return "\n\n---\n\n".join(
        chunk.content
        for chunk in chunks
    )