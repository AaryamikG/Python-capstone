def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Paragraph-aware fixed-size chunking with overlap, so chunks don't split mid-sentence
    unless a single paragraph itself exceeds chunk_size."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in paragraphs:
        if buf and len(buf) + len(para) + 1 > chunk_size:
            chunks.append(buf)
            tail = buf[-overlap:] if overlap else ""
            buf = f"{tail}\n{para}".strip()
        else:
            buf = f"{buf}\n{para}".strip() if buf else para
    if buf:
        chunks.append(buf)
    return chunks
