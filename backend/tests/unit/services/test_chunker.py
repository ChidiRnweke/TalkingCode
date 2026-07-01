from talkingcode.services.ingestion.chunker import LineChunker


def test_chunker_produces_chunks():
    chunker = LineChunker()
    chunks = chunker.chunk("line1\nline2\nline3")
    assert len(chunks) >= 1
