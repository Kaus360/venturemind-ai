"""Text chunking utilities for startup intelligence embeddings.

Long startup descriptions, pitch-deck extracts, and market narratives should be
split into overlapping chunks before embedding so semantic search can retrieve
focused passages instead of only whole-document vectors.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, Field, field_validator

from backend.vectorstore.embedding_pipeline import generate_batch_embeddings

DEFAULT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", "800"))
DEFAULT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", "120"))


class ChunkingError(ValueError):
    """Raised when text chunking receives invalid input or configuration."""


class TextChunks(BaseModel):
    """Structured chunking result for downstream services."""

    chunks: list[str] = Field(default_factory=list)
    chunk_size: int
    overlap: int


class ChunkEmbeddings(BaseModel):
    """Structured chunk-and-embed result."""

    chunks: list[str] = Field(default_factory=list)
    embeddings: list[list[float]] = Field(default_factory=list)

    @field_validator("embeddings")
    @classmethod
    def validate_embeddings(cls, embeddings: list[list[float]]) -> list[list[float]]:
        """Ensure the embedding result shape is a list of vector lists."""

        if any(not embedding for embedding in embeddings):
            raise ValueError("embeddings must not contain empty vectors.")
        return embeddings


def _validate_chunk_config(chunk_size: int, overlap: int) -> None:
    """Validate chunk size and overlap before splitting text."""

    if chunk_size < 1:
        raise ChunkingError("chunk_size must be greater than zero.")

    if overlap < 0:
        raise ChunkingError("overlap must be zero or greater.")

    if overlap >= chunk_size:
        raise ChunkingError("overlap must be smaller than chunk_size.")


def _normalize_text(text: str) -> str:
    """Collapse whitespace while preserving word order."""

    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    return " ".join(text.split())


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping character chunks.

    Args:
        text: Source text to split.
        chunk_size: Maximum number of characters in each chunk.
        overlap: Number of characters retained between adjacent chunks.

    Returns:
        A list of clean text chunks. Empty or whitespace-only text returns an
        empty list, and text shorter than ``chunk_size`` returns a single chunk.
    """

    _validate_chunk_config(chunk_size=chunk_size, overlap=overlap)
    normalized_text = _normalize_text(text)

    if not normalized_text:
        return []

    if len(normalized_text) <= chunk_size:
        return [normalized_text]

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap

    while start < len(normalized_text):
        end = min(start + chunk_size, len(normalized_text))
        chunk = normalized_text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(normalized_text):
            break

        start += step

    return chunks


async def chunk_and_embed(text: str) -> list[list[float]]:
    """Chunk text and generate one embedding for each chunk.

    Empty text produces an empty list so callers can safely skip vector upserts
    when no meaningful source content exists.
    """

    chunks = chunk_text(text)
    if not chunks:
        return []

    return await generate_batch_embeddings(chunks)


async def chunk_and_embed_with_metadata(text: str) -> ChunkEmbeddings:
    """Chunk text and return both chunks and generated embeddings."""

    chunks = chunk_text(text)
    if not chunks:
        return ChunkEmbeddings(chunks=[], embeddings=[])

    embeddings = await generate_batch_embeddings(chunks)
    return ChunkEmbeddings(chunks=chunks, embeddings=embeddings)
