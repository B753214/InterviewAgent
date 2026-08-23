import asyncio

from backend.app.agent.schemas.material import MaterialCreate
from backend.app.database import AsyncSessionLocal, init_db
from backend.app.rag.milvus_store import ensure_collection
from backend.app.services import material_service


async def main():
    await init_db()
    ensure_collection()
    async with AsyncSessionLocal() as db:
        mat = await material_service.create_material(
            db,
            MaterialCreate(
                name="FastAPI笔记",
                raw_text="# 依赖注入\n\nFastAPI 使用 Depends()。\n\n# Redis\n\nredis-py 缓存。",
            ),
        )
        print("id:", mat.id)
        print("chunk_count:", mat.chunk_count)
        print("status:", mat.embedding_status)


asyncio.run(main())