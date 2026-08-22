"""Authentication Service."""
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.auth import get_password_hash, verify_password, create_access_token
from backend.app.core.exceptions import SentinelAIException
from backend.app.models.user import User
from backend.app.models.organization import OrganizationRole
from backend.app.repositories.user_repo import UserRepository
from backend.app.repositories.org_repo import OrganizationRepository
from backend.app.services.audit_service import AuditService
from backend.app.schemas.auth import TokenResponse, UserResponse, OrgMembershipBrief


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.audit_service = AuditService(db)

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        organization_name: str,
        ip_address: Optional[str] = None
    ) -> TokenResponse:
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise SentinelAIException("Email address is already registered.", status_code=400, code="EMAIL_ALREADY_EXISTS")

        # 1. Create User
        hashed_password = get_password_hash(password)
        user = await self.user_repo.create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name
        )

        # 2. Provision Default Organization
        org = await self.org_repo.create(
            name=organization_name,
            description=f"Primary organization workspace for {full_name}"
        )

        # 3. Add User as ORGANIZATION_ADMIN
        await self.org_repo.add_member(
            org_id=org.id,
            user_id=user.id,
            role=OrganizationRole.ORGANIZATION_ADMIN
        )

        # 4. Audit Log
        await self.audit_service.log_event(
            org_id=org.id,
            action="REGISTRATION",
            resource_type="USER",
            resource_id=user.id,
            user_id=user.id,
            details={"email": user.email, "organization_name": org.name},
            ip_address=ip_address
        )

        await self.db.commit()

        # 5. Issue JWT Token
        token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "org_id": org.id,
            "role": OrganizationRole.ORGANIZATION_ADMIN.value
        })

        return TokenResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            default_organization_id=org.id
        )

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> TokenResponse:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise SentinelAIException("Invalid email or password.", status_code=401, code="INVALID_CREDENTIALS")

        if not user.is_active:
            raise SentinelAIException("User account is inactive. Please contact support.", status_code=403, code="ACCOUNT_INACTIVE")

        org_memberships = await self.org_repo.get_user_organizations(user.id)
        if not org_memberships:
            raise SentinelAIException("User has no active organization memberships.", status_code=403, code="NO_ORGANIZATION")

        primary_org, primary_role = org_memberships[0]

        await self.audit_service.log_event(
            org_id=primary_org.id,
            action="LOGIN",
            resource_type="USER",
            resource_id=user.id,
            user_id=user.id,
            details={"email": user.email},
            ip_address=ip_address
        )

        await self.db.commit()

        token = create_access_token({
            "sub": user.id,
            "email": user.email,
            "org_id": primary_org.id,
            "role": primary_role.value
        })

        return TokenResponse(
            access_token=token,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            default_organization_id=primary_org.id
        )

    async def get_current_user_profile(self, user_id: str) -> UserResponse:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise SentinelAIException("User not found.", status_code=404, code="USER_NOT_FOUND")

        org_memberships = await self.org_repo.get_user_organizations(user.id)
        memberships_dto = [
            OrgMembershipBrief(
                organization_id=org.id,
                organization_name=org.name,
                organization_slug=org.slug,
                role=role
            )
            for org, role in org_memberships
        ]

        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
            memberships=memberships_dto
        )
