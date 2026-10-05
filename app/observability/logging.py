import logging
import time
from contextlib import asynccontextmanager


logger = logging.getLogger(
    "mini_ai_platform"
)


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
    )


@asynccontextmanager
async def track_operation(
    operation: str,
):
    started = time.perf_counter()

    logger.info(
        "operation_started=%s",
        operation,
    )

    try:
        yield

    except Exception:
        elapsed = time.perf_counter() - started

        logger.exception(
            "operation_failed=%s duration=%.3f",
            operation,
            elapsed,
        )

        raise

    else:
        elapsed = time.perf_counter() - started

        logger.info(
            "operation_completed=%s duration=%.3f",
            operation,
            elapsed,
        )