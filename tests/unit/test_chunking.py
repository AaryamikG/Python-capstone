from enterprise_rag.vectorstore.chunking import chunk_text


def test_empty_document_produces_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []


def test_short_document_is_a_single_chunk():
    text = "Paragraph one.\n\nParagraph two."
    chunks = chunk_text(text, chunk_size=800, overlap=150)
    assert len(chunks) == 1
    assert "Paragraph one." in chunks[0]
    assert "Paragraph two." in chunks[0]


def test_long_document_splits_into_multiple_chunks_with_overlap():
    paragraphs = [f"Paragraph {i} " + ("word " * 30) for i in range(10)]
    text = "\n\n".join(paragraphs)

    chunks = chunk_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 200 + 50 + 20  # allow slack for the carried-over overlap tail
    # Overlap: the tail of one chunk should reappear at the start of the next.
    assert chunks[0][-50:].strip()[:20] in chunks[1]
