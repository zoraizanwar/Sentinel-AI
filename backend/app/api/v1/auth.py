"""Authentication Endpoints."""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.services.auth_service import AuthService
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Registers a new user and provisions their initial organization with ORGANIZATION_ADMIN role."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    return await service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        organization_name=payload.organization_name,
        ip_address=ip_address
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    payload: UserLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Authenticates user credentials and issues a signed JWT token."""
    service = AuthService(db)
    ip_address = request.client.host if request.client else None
    return await service.login(
        email=payload.email,
        password=payload.password,
        ip_address=ip_address
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Fetches the current authenticated user's profile and active organization memberships."""
    service = AuthService(db)
    return await service.get_current_user_profile(current_user.id)
