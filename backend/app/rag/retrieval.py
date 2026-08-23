import json
import sqlite3

from backend.app.config import PROJECT_ROOT
from backend.app.rag.embeddings import embed_text_sync
from backend.app.rag.milvus_store import search_chunk


def _load_chunks_by_ids_sync(chunk_ids: list[str]) -> dict[str, dict]:
    if not chunk_ids:
        return {}
    db_path = PROJECT_ROOT / "interview.db"
    placeholders = ",".join("?" for _ in chunk_ids)
    sql = f"""
            SELECT id, content, metadata_json
            FROM material_chunks
            WHERE id IN ({placeholders})
        """
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(sql, chunk_ids).fetchall()
    finally:
        conn.close()
    result = {}
    for chunk_id, content, metadata_json in rows:
        metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else (metadata_json or {})
        result[chunk_id] = {"content": content, "metadata_json": metadata}
    return result


def retrieve_material_context(query_text: str, material_ids: list[str], *, top_k: int = 2) -> list[dict]:
    """RAG 检索占位：M4 前返回空列表。"""
    if not query_text.strip() or not material_ids:
        return []
    query_vector = embed_text_sync(query_text)
    hits = search_chunk(query_vector, material_ids, top_k=top_k)
    if not hits:
        return []
    chunk_map = _load_chunks_by_ids_sync([hit["id"] for hit in hits])
    results = []
    for hit in hits:
        row = chunk_map.get(hit["id"])
        if row is None:
            continue
        results.append({
            "id": hit["id"],
            "material_id": hit["material_id"],
            "chunk_index": hit["chunk_index"],
            "content": row["content"],
            "metadata_json": row["metadata_json"],
            "score": hit.get("score"),
        })
    return results


def format_context(chunks: list[dict]) -> str:
    lines = []
    for chunk in chunks:
        metadata = chunk.get("metadata_json") or chunk.get("metadata") or {}
        heading = metadata.get("heading", "")
        label = f"资料片段 {chunk.get('chunk_index', '-')}"
        if heading:
            label += f" / {heading}"
        lines.append(f"[{label}]\n{chunk.get('content', '').strip()}")
    return "\n---\n".join(lines)
