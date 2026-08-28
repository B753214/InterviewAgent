from pathlib import Path

from pypdf import PdfReader


def extract_pdf_text(pdf_path: Path, max_pages: int = 30) -> str:
    reader = PdfReader(str(pdf_path))
    pages = reader.pages[:max_pages]
    parts: list[str] = []
    for i, page in enumerate(pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            parts.append(f"## Page {i}\n\n{text}")
    markdown = "\n\n".join(parts).strip()
    if not markdown:
        raise ValueError("PDF 未能提取到文本（可能是扫描件，需后续 vision）")
    if len(reader.pages) > max_pages:
        markdown += f"\n\n> 仅处理前 {max_pages} 页。"
    return markdown