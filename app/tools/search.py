from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.retriever import retrieve_chunks


async def search_documents(
    db: AsyncSession,
    query: str,
    limit: int = 5,
) -> list[dict]:
    chunks = await retrieve_chunks(
        db=db,
        question=query,
        limit=limit,
    )

    return [
        {
            "document_id": chunk.document_id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
        }
        for chunk in chunks
    ]