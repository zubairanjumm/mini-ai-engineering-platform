from app.rag.generator import generate_embedding


async def create_embeddings(
    chunks: list[str],
) -> list[list[float]]:
    embeddings = []

    for chunk in chunks:
        embedding = await generate_embedding(chunk)
        embeddings.append(embedding)

    return embeddings