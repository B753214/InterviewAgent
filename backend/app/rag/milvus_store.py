from functools import lru_cache

from pymilvus import MilvusClient, DataType

from backend.app.config import settings

COLLECTION_NAME = settings.MILVUS_COLLECTION
DIM = settings.EMBEDDING_DIMENSIONS

@lru_cache
def get_client()->MilvusClient:
    return MilvusClient(uri=settings.MILVUS_URI)

def ensure_collection()->None:
    client = get_client()
    if client.has_collection(COLLECTION_NAME):
        return
    schema=MilvusClient.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field(field_name="id", datatype=DataType.VARCHAR, is_primary=True, max_length=64)
    schema.add_field(field_name="material_id", datatype=DataType.VARCHAR, max_length=64)
    schema.add_field(field_name="chunk_index", datatype=DataType.INT64)
    schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=DIM)
    index_params = client.prepare_index_params()
    index_params.add_index(field_name="vector", index_type="AUTOINDEX", metric_type="COSINE")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        schema=schema,
        index_params=index_params,
    )

def upsert_chunk(rows: list[dict])->None:
    if not rows:
        return
    get_client().upsert(
        collection_name=COLLECTION_NAME,
        data=rows,
    )
def search_chunk(
    query_vector: list[float],
    material_ids: list[str],
    *,
    top_k: int = 2,
) -> list[dict]:
    if not material_ids:
        return []
    ids_literal = ", ".join(f'"{mid}"' for mid in material_ids)
    filter_expr = f"material_id in [{ids_literal}]"
    results = get_client().search(
        collection_name=COLLECTION_NAME,
        data=[query_vector],
        filter=filter_expr,
        limit=top_k,
        output_fields=["material_id", "chunk_index"],
    )
    hits = []
    for group in results:
        for hit in group:
            entity = hit.get("entity") or {}
            hits.append({
                "id": hit["id"],
                "material_id": entity.get("material_id"),
                "chunk_index": entity.get("chunk_index"),
                "score": hit.get("distance"),
            })
    return hits

def delete_by_material_id(material_id: str) -> None:
    get_client().delete(
        collection_name=COLLECTION_NAME,
        filter=f'material_id == "{material_id}"',
    )

