import asyncio
from backend.app.db.session import AsyncSessionLocal, init_db
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User
from sqlalchemy import select

async def main():
    await init_db()
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.email == "admin@sentinel.ai"))
        existing = res.scalar_one_or_none()
        if not existing:
            auth_service = AuthService(db)
            token_resp = await auth_service.register(
                email="admin@sentinel.ai",
                password="SentinelAdmin2026!",
                full_name="Sentinel Admin",
                organization_name="Sentinel Risk Operations"
            )
            print(f"Default admin created successfully! Email: {token_resp.email}, Org ID: {token_resp.default_organization_id}")
        else:
            print(f"Admin already exists: {existing.email}")

if __name__ == "__main__":
    asyncio.run(main())
