from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router


app = FastAPI(
    title="Mini AI Engineering Platform",
    version="0.1.0",
)


app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    return {
        "name": "Mini AI Engineering Platform",
        "status": "running",
    }