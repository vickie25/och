"""
Schemas for AI profiling system.
"""
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

if TYPE_CHECKING:
    from .profiling_tracks import TrackInfo
else:
    # Import TrackInfo from profiling_tracks to avoid circular imports
    from .profiling_tracks import TrackInfo


class QuestionOption(BaseModel):
    """An option for a profiling question."""
    value: str
    text: str
    scores: dict[str, int]  # Track scores like {"defender": 3, "offensive": 2}


class ProfilingQuestion(BaseModel):
    """A profiling question with multiple choice options."""
    id: str
    question: str
    category: str  # technical_aptitude, problem_solving, scenario_preference, work_style, cybersecurity_mindset
    options: list[QuestionOption]


class ProfilingResponse(BaseModel):
    """User's response to a profiling question."""
    question_id: str
    selected_option: str
    response_time_ms: int | None = None


class SubmitResponseRequest(BaseModel):
    """Request model for submitting a profiling question response."""
    question_id: str
    selected_option: str


class ProfilingSession(BaseModel):
    """A complete profiling session."""
    id: str
    user_id: int  # Django uses integer user IDs, not UUIDs
    responses: list[ProfilingResponse]
    started_at: datetime
    completed_at: datetime | None = None
    scores: dict[str, float] | None = None
    recommended_track: str | None = None

    # Anti-cheat fields (optional, added dynamically)
    ip_address: str | None = None
    user_agent: str | None = None
    device_fingerprint: str | None = None
    response_times: list[dict[str, Any]] | None = None
    suspicious_patterns: list[str] | None = None
    anti_cheat_score: float | None = None

    # Telemetry and metadata (optional, added dynamically)
    telemetry: dict[str, Any] | None = None
    difficulty_verification: dict[str, Any] | None = None
    reflection_responses: dict[str, Any] | None = None

    class Config:
        arbitrary_types_allowed = True


class TrackRecommendation(BaseModel):
    """Recommendation result for a track."""
    track_key: str
    track_name: str
    score: float
    confidence_level: str  # high, medium, low
    reasoning: list[str]
    career_suggestions: list[str]
    strengths_aligned: list[str]  # Strengths that align with this track
    optimal_path: str  # Recommended learning path


class DeepInsights(BaseModel):
    """Deep insights about the user's profile."""
    primary_strengths: list[str]
    learning_preferences: dict[str, Any]
    career_alignment: dict[str, Any]
    optimal_learning_path: list[str]
    recommended_foundations: list[str]
    growth_opportunities: list[str]
    personality_traits: dict[str, Any]


class ProfilingResult(BaseModel):
    """Complete profiling result."""
    user_id: int  # Django uses integer user IDs, not UUIDs
    session_id: str
    recommendations: list[TrackRecommendation]
    primary_track: TrackInfo
    secondary_track: TrackInfo | None = None
    assessment_summary: str
    deep_insights: DeepInsights | None = None
    completed_at: datetime

    # AI-powered enhancements
    future_you_persona: dict[str, Any] | None = None  # AI-generated Future-You persona
    personalized_track_descriptions: dict[str, str] | None = None  # Track-specific personalized descriptions
    ai_confidence: float | None = None  # AI recommendation confidence (0-1)
    ai_reasoning: str | None = None  # AI's reasoning for the recommendation


class ProfilingProgress(BaseModel):
    """Current progress in profiling session."""
    session_id: str
    current_question: int
    total_questions: int
    progress_percentage: float
    estimated_time_remaining: int  # seconds


# Export OCH_TRACKS from profiling_tracks module
# This ensures backward compatibility while using the correct 5 tracks
__all__ = [
    'TrackInfo',
    'QuestionOption',
    'ProfilingQuestion',
    'ProfilingResponse',
    'SubmitResponseRequest',
    'ProfilingSession',
    'TrackRecommendation',
    'DeepInsights',
    'ProfilingResult',
    'ProfilingProgress',
    'OCH_TRACKS',
]
