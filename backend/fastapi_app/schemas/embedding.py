"""
Embedding API schemas.
"""

from pydantic import BaseModel


class EmbeddingItem(BaseModel):
    """
    Single embedding item with text and vector.
    """
    text: str
    embedding: list[float]


class EmbeddingRequest(BaseModel):
    """
    Request schema for embedding generation.
    """
    texts: list[str]


class EmbeddingResponse(BaseModel):
    """
    Response schema for embeddings.
    """
    embeddings: list[EmbeddingItem]
    model: str
    dimension: int


