from openai import AsyncOpenAI

from app.core.config import settings


client = AsyncOpenAI(
    api_key=settings.openai_api_key,
)


async def generate_embedding(text: str) -> list[float]:
    response = await client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )

    return response.data[0].embedding


async def generate_answer(
    question: str,
    context: str,
) -> str:
    prompt = f"""
You are an AI assistant that answers questions using the provided
document context.

Document context:
{context}

User question:
{question}

Instructions:
- Answer using the provided context.
- If the context does not contain enough information, say so.
- Do not invent facts.
- Give a clear and concise answer.
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
    )

    return response.choices[0].message.content or ""