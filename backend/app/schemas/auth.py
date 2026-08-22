"""Authentication and User Pydantic Schemas."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from backend.app.models.organization import OrganizationRole


class UserRegisterRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255, description="User email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    full_name: str = Field(..., min_length=1, max_length=255)
    organization_name: str = Field(..., min_length=1, max_length=255, description="Initial organization to provision")


class UserLoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    default_organization_id: str


class OrgMembershipBrief(BaseModel):
    organization_id: str
    organization_name: str
    organization_slug: str
    role: OrganizationRole


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    is_active: bool
    created_at: datetime
    memberships: List[OrgMembershipBrief] = []

    model_config = {"from_attributes": True}
