"""
Recommendation API schemas.
"""

from pydantic import BaseModel


class RecommendationItem(BaseModel):
    """
    Single recommendation item.
    """
    content_id: str
    content_type: str
    title: str
    description: str | None = None
    score: float
    reason: str | None = None


class RecommendationRequest(BaseModel):
    """
    Request schema for recommendations.
    """
    user_id: int
    content_type: str | None = None
    limit: int = 10


class RecommendationResponse(BaseModel):
    """
    Response schema for recommendations.
    """
    user_id: int
    recommendations: list[RecommendationItem]
    total: int


