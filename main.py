from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.rag.milvus_store import ensure_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    ensure_collection()
    yield
    from backend.app.database import engine
    await engine.dispose()

app=FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.api.interview import router as interview_router
from backend.app.api.jobs import router as jobs_router
from backend.app.api.resumes import router as resumes_router
from backend.app.api.materials import router as material_router
from backend.app.api.memory import router as memory_router
app.include_router(memory_router, prefix="/memories")
app.include_router(interview_router, prefix="/interviews")
app.include_router(jobs_router, prefix="/jobs")
app.include_router(resumes_router, prefix="/resumes")
app.include_router(material_router, prefix="/materials")


@app.get("/")
async def root():
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health")
async def health():
    return {"status": "ok", "name": settings.APP_NAME, "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)