"""Organization Repository for Tenant Isolation & Membership Operations."""
from typing import List, Optional, Tuple
import re
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.organization import Organization, OrganizationMember, OrganizationRole
from backend.app.models.user import User


def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    return re.sub(r"[-\s]+", "-", slug)


class OrganizationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, org_id: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.id == org_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        stmt = select(Organization).where(Organization.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_organizations(self, user_id: str) -> List[Tuple[Organization, OrganizationRole]]:
        stmt = (
            select(Organization, OrganizationMember.role)
            .join(OrganizationMember, Organization.id == OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
            .order_by(Organization.name)
        )
        result = await self.db.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def get_member(self, org_id: str, user_id: str) -> Optional[OrganizationMember]:
        stmt = select(OrganizationMember).where(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == user_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_members_with_users(self, org_id: str) -> List[OrganizationMember]:
        stmt = (
            select(OrganizationMember)
            .options(joinedload(OrganizationMember.user))
            .where(OrganizationMember.organization_id == org_id)
            .order_by(OrganizationMember.created_at)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, name: str, description: Optional[str] = None, slug: Optional[str] = None) -> Organization:
        base_slug = slug or slugify(name)
        candidate_slug = base_slug
        count = 1
        
        while await self.get_by_slug(candidate_slug):
            candidate_slug = f"{base_slug}-{count}"
            count += 1

        org = Organization(
            name=name.strip(),
            slug=candidate_slug,
            description=description.strip() if description else None
        )
        self.db.add(org)
        await self.db.flush()
        return org

    async def add_member(self, org_id: str, user_id: str, role: OrganizationRole) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=role
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def remove_member(self, member: OrganizationMember) -> None:
        await self.db.delete(member)
        await self.db.flush()
