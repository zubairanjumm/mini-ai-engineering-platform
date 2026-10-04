from fastapi import FastAPI

app = FastAPI(
    title="Mini AI Engineering Platform",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {
        "name": "Mini AI Engineering Platform",
        "status": "running",
    }