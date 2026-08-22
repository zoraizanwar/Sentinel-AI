"""FastAPI Dependency Providers for Authentication, Tenancy & Database."""
from typing import AsyncGenerator, Optional, List, Tuple
from fastapi import Depends, Header, HTTPException, status, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db
from backend.app.core.auth import decode_access_token
from backend.app.core.exceptions import SentinelAIException
from backend.app.models.user import User
from backend.app.models.organization import Organization, OrganizationMember, OrganizationRole
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.core.session_store import session_store, SessionStore
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.reporting.pdf_report import PDFReportGenerator

security_scheme = HTTPBearer(auto_error=False)


def get_session_store() -> SessionStore:
    """Returns the singleton in-memory session store."""
    return session_store


def get_analysis_service() -> AnalysisService:
    """Provides singleton/instance AnalysisService for session-based workflows."""
    return AnalysisService()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extracts and verifies current user from Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_access_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or no longer exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


class OrgContextChecker:
    """
    Enforces strict tenant isolation and RBAC role validation for organization endpoints.
    Ensures that a user belonging to Org A cannot access Org B's resources.
    """
    def __init__(self, allowed_roles: Optional[List[OrganizationRole]] = None):
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        org_id: str = Path(..., description="Organization UUID"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> Tuple[Organization, OrganizationMember]:
        org_repo = OrganizationRepository(db)
        
        # 1. Check organization exists
        org = await org_repo.get_by_id(org_id)
        if not org:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization '{org_id}' not found."
            )

        # 2. Check user membership in requested organization (Strict Tenant Isolation)
        member = await org_repo.get_member(org_id=org_id, user_id=current_user.id)
        if not member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You are not a member of this organization."
            )

        # 3. Check RBAC permissions if roles are restricted
        if self.allowed_roles and member.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Action requires one of {[r.value for r in self.allowed_roles]}, but user has '{member.role.value}'."
            )

        return org, member


# Convenience dependency factories for RBAC
require_org_member = OrgContextChecker()
require_org_analyst = OrgContextChecker(allowed_roles=[OrganizationRole.ORGANIZATION_ADMIN, OrganizationRole.ANALYST])
require_org_admin = OrgContextChecker(allowed_roles=[OrganizationRole.ORGANIZATION_ADMIN])
