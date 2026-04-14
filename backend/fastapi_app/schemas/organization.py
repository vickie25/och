"""
Organization schemas matching Django serializers.
"""
from datetime import datetime

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    """
    Base organization schema matching Django OrganizationBaseSchema.
    """
    name: str
    slug: str
    description: str | None = None
    logo_url: str | None = None
    website: str | None = None


class OrganizationResponse(OrganizationBase):
    """
    Organization response schema matching Django OrganizationResponseSchema.
    """
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


