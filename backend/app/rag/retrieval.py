def retrieve_material_context(query_text:str, material_ids:list[str], *, top_k: int=2)->list[dict]:
    pass

def format_context(chunks: list[dict]) -> str:
    lines=[]
    for chunk in chunks:
        metadata = chunk.get("metadata_json") or chunk.get("metadata") or {}
        heading = metadata.get("heading", "")
        label = f"资料片段 {chunk.get('chunk_index', '-')}"
        if heading:
            label += f" / {heading}"
        lines.append(f"[{label}]\n{chunk.get('content', '').strip()}")
    return "\n---\n".join(lines)