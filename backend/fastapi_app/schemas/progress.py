"""
Progress schemas matching Django serializers.
"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ProgressBase(BaseModel):
    """
    Base progress schema matching Django ProgressBaseSchema.
    """
    content_id: str
    content_type: str
    status: Literal["not_started", "in_progress", "completed", "paused"]
    completion_percentage: int = 0
    score: float | None = None
    metadata: dict = {}


class ProgressResponse(ProgressBase):
    """
    Progress response schema matching Django ProgressResponseSchema.
    """
    id: int
    user_id: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


