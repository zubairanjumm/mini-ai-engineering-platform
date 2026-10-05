from openai import AsyncOpenAI

from app.core.config import settings


client = AsyncOpenAI(
    api_key=settings.openai_api_key,
)


async def generate_embedding(
    text: str,
) -> list[float]:
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )

    return response.data[0].embedding


async def generate_answer(
    question: str,
    context: str,
) -> str:
    prompt = f"""
You are an AI assistant inside a document intelligence platform.

Use the supplied document context and conversation history
to answer the user's question.

DOCUMENT AND CONVERSATION CONTEXT:
{context}

USER QUESTION:
{question}

Rules:
- Use the supplied context whenever possible.
- Do not invent information.
- If the context does not contain enough information, say that clearly.
- Give a direct and useful answer.
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You answer questions accurately using "
                    "provided context."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.choices[0].message.content or ""