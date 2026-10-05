from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Evaluation


def calculate_context_overlap(
    answer: str,
    context: str,
) -> float:
    answer_words = {
        word.lower().strip(".,!?")
        for word in answer.split()
        if len(word) > 3
    }

    context_words = {
        word.lower().strip(".,!?")
        for word in context.split()
        if len(word) > 3
    }

    if not answer_words:
        return 0.0

    overlap = answer_words.intersection(
        context_words
    )

    return len(overlap) / len(answer_words)


async def save_evaluation(
    db: AsyncSession,
    conversation_id: int,
    question: str,
    answer: str,
    context: str,
) -> Evaluation:
    score = calculate_context_overlap(
        answer=answer,
        context=context,
    )

    feedback = (
        "Answer has strong contextual overlap."
        if score >= 0.5
        else "Answer has limited contextual overlap."
    )

    evaluation = Evaluation(
        conversation_id=conversation_id,
        question=question,
        answer=answer,
        score=score,
        feedback=feedback,
    )

    db.add(evaluation)

    await db.commit()
    await db.refresh(evaluation)

    return evaluation