"""
Personality analysis API schemas.
"""

from pydantic import BaseModel

from schemas.progress import ProgressResponse


class PersonalityAnalysisRequest(BaseModel):
    """
    Request schema for personality analysis.
    """
    user_id: int
    progress_data: list[ProgressResponse] | None = None


class PersonalityTrait(BaseModel):
    """
    Single personality trait.
    """
    name: str
    score: float
    description: str | None = None


class PersonalityAnalysisResponse(BaseModel):
    """
    Response schema for personality analysis.
    """
    user_id: int
    traits: list[PersonalityTrait]
    summary: str | None = None
    recommendations: list[str] | None = None


