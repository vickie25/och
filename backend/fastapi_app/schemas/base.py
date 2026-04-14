"""
Base Pydantic schemas shared across the application.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema with common configuration.
    """
    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """
    Base schema with timestamp fields.
    """
    created_at: datetime
    updated_at: datetime


