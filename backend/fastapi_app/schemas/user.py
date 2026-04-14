"""
User schemas matching Django serializers.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """
    Base user schema matching Django UserBaseSchema.
    """
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    bio: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """
    User response schema matching Django UserResponseSchema.
    """
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }


