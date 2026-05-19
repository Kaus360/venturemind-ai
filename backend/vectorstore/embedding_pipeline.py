"""Sentence-transformers embedding service for semantic search.

The service lazily loads ``sentence-transformers/all-MiniLM-L6-v2`` and exposes
async methods so FastAPI routes can generate embeddings without blocking the
event loop. The model itself is CPU/GPU-bound and synchronous, so encoding work
is delegated to a worker thread with ``asyncio.to_thread``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Final

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL: Final[str] = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION: Final[int] = 384


class EmbeddingPipelineError(RuntimeError):
    """Raised when the embedding pipeline cannot load or encode input."""


class EmbeddingPipeline:
    """Lazy, async-ready wrapper around a sentence-transformers model."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL) -> None:
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self._load_lock = asyncio.Lock()

    async def load_model(self) -> SentenceTransformer:
        """Load and cache the embedding model once per process."""

        if self._model is not None:
            return self._model

        async with self._load_lock:
            if self._model is not None:
                return self._model

            try:
                logger.info("Loading embedding model: %s", self.model_name)
                self._model = await asyncio.to_thread(SentenceTransformer, self.model_name)
            except Exception as exc:
                logger.exception("Failed to load embedding model: %s", self.model_name)
                raise EmbeddingPipelineError("Failed to load embedding model.") from exc

            return self._model

    async def generate_embedding(self, text: str) -> list[float]:
        """Generate a normalized embedding vector for one text input."""

        cleaned_text = self._validate_text(text)
        model = await self.load_model()

        try:
            embedding = await asyncio.to_thread(
                model.encode,
                cleaned_text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embedding.astype(float).tolist()
        except Exception as exc:
            logger.exception("Failed to generate embedding for text input.")
            raise EmbeddingPipelineError("Failed to generate embedding.") from exc

    async def generate_batch_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embedding vectors for a batch of text inputs."""

        cleaned_texts = self._validate_texts(texts)
        model = await self.load_model()

        try:
            embeddings = await asyncio.to_thread(
                model.encode,
                cleaned_texts,
                batch_size=32,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
            return embeddings.astype(float).tolist()
        except Exception as exc:
            logger.exception("Failed to generate batch embeddings.")
            raise EmbeddingPipelineError("Failed to generate batch embeddings.") from exc

    @staticmethod
    def _validate_text(text: str) -> str:
        """Validate and normalize a single text value before embedding."""

        if not isinstance(text, str):
            raise TypeError("text must be a string.")

        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("text must not be empty.")

        return cleaned_text

    @classmethod
    def _validate_texts(cls, texts: list[str]) -> list[str]:
        """Validate and normalize a batch of text values before embedding."""

        if not texts:
            raise ValueError("texts must contain at least one item.")

        return [cls._validate_text(text) for text in texts]


embedding_pipeline = EmbeddingPipeline()


async def generate_embedding(text: str) -> list[float]:
    """Module-level convenience wrapper for single-text embedding."""

    return await embedding_pipeline.generate_embedding(text)


async def generate_batch_embeddings(texts: list[str]) -> list[list[float]]:
    """Module-level convenience wrapper for batch embedding."""

    return await embedding_pipeline.generate_batch_embeddings(texts)
