import asyncio
import os
import sys

from sqlalchemy import text

sys.path.append(os.getcwd())

from app.admin.models import Admin
from app.admin.utils import get_password_hash
from app.config import settings
from app.database import async_session_maker

async def create_admin():
    admin_username = settings.ADMIN_USERNAME
    admin_password = settings.ADMIN_PASSWORD

    async with async_session_maker() as session:
        async with session.begin():
            result = await session.execute(
                text("SELECT 1 FROM admin WHERE username = :username"),
                {"username": admin_username},
            )
            if result.scalar():
                print("Admin already exists")
                return

            hashed_password = get_password_hash(admin_password)
            new_admin = Admin(
                username=admin_username,
                hashed_password=hashed_password,
            )
            session.add(new_admin)
            print("Admin created successfully")


if __name__ == "__main__":
    asyncio.run(create_admin())