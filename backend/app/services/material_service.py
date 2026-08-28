import shutil
import uuid
from datetime import datetime

from fastapi import UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.schemas.material import MaterialCreate, MaterialResponse
from backend.app.config import DATA_DIR
from backend.app.models.material import MaterialORM
from backend.app.models.material_chunk import MaterialChunkORM
from backend.app.rag.chunking import chunk_text
from backend.app.rag.embeddings import embed_texts_sync, embedding_backend
from backend.app.rag.milvus_store import delete_by_material_id, upsert_chunk
from backend.app.services.pdf_service import extract_pdf_text


def _orm_to_material(row: MaterialORM) -> MaterialResponse:
    return MaterialResponse(
        id=row.id,
        name=row.name,
        type=row.type or "markdown",
        raw_text=row.raw_text,
        source_file_path=row.source_file_path,
        markdown_path=row.markdown_path or "",
        enabled=row.enabled,
        chunk_count=row.chunk_count,
        embedding_status=row.embedding_status,
        processing_error=row.processing_error or "",
        created_at=row.created_at,
    )


async def create_material(db: AsyncSession, data: MaterialCreate) -> MaterialResponse:
    now = datetime.now().isoformat()
    row = MaterialORM(
        name=data.name,
        type=data.type,
        raw_text=data.raw_text,
        markdown_path="",
        embedding_status="indexing",
        created_at=now,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    row = await _index_material_text(db, row, data.raw_text)
    return _orm_to_material(row)


async def create_pdf_material(db: AsyncSession, name: str, upload: UploadFile) -> MaterialResponse:
    filename = upload.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported")
    now = datetime.now().isoformat()
    row = MaterialORM(
        name=name,
        type="pdf",
        raw_text="",
        source_file_path = "",
        markdown_path="",
        embedding_status="extracting",
        created_at=now,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    upload_dir = DATA_DIR / "material_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / f"{row.id}.pdf"
    with target_path.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    row.source_file_path = str(target_path)
    await db.commit()

    try:
        text = extract_pdf_text(target_path)
        row = await _index_material_text(db, row, text)
        return _orm_to_material(row)
    except Exception as exc:
        row.embedding_status = "failed"
        row.processing_error = f"{type(exc).__name__}: {exc}"
        await db.commit()
        await db.refresh(row)
        return _orm_to_material(row)




async def _index_material_text(
    db: AsyncSession,
    material: MaterialORM,
    raw_text: str,
) -> MaterialORM:
    chunks = chunk_text(raw_text)

    delete_by_material_id(material.id)
    await db.execute(
        delete(MaterialChunkORM).where(MaterialChunkORM.material_id == material.id)
    )

    milvus_rows: list[dict] = []
    now = datetime.now().isoformat()
    backend = embedding_backend()

    if not chunks:
        vectors: list[list[float]] = []
    else:
        vectors = embed_texts_sync([chunk["content"] for chunk in chunks])

    for chunk, vector in zip(chunks, vectors):
        chunk_id = str(uuid.uuid4())
        metadata = {
            **chunk.get("metadata", {}),
            "embedding_backend": backend,
        }

        db.add(MaterialChunkORM(
            id=chunk_id,
            material_id=material.id,
            chunk_index=metadata["chunk_index"],
            content=chunk["content"],
            metadata_json=metadata,
            created_at=now,
        ))

        milvus_rows.append({
            "id": chunk_id,
            "material_id": material.id,
            "chunk_index": metadata["chunk_index"],
            "vector": vector,
        })

    upsert_chunk(milvus_rows)

    material.raw_text = raw_text
    material.chunk_count = len(chunks)
    material.embedding_status = "ready" if chunks else "empty"
    material.processing_error = ""

    await db.commit()
    await db.refresh(material)
    return material


async def list_materials(db: AsyncSession) -> list[MaterialResponse]:
    result = await db.execute(
        select(MaterialORM).order_by(MaterialORM.created_at.desc())
    )
    return [_orm_to_material(row) for row in result.scalars().all()]


async def get_material(db: AsyncSession, material_id: str) -> MaterialResponse | None:
    row = await db.get(MaterialORM, material_id)
    return _orm_to_material(row) if row else None


async def get_chunks_by_ids(
    db: AsyncSession,
    chunk_ids: list[str],
) -> dict[str, MaterialChunkORM]:
    if not chunk_ids:
        return {}
    result = await db.execute(
        select(MaterialChunkORM).where(MaterialChunkORM.id.in_(chunk_ids))
    )
    return {row.id: row for row in result.scalars().all()}
