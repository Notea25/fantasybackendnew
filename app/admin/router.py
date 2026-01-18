from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.admin.dependencies import get_db
from app.admin.models import Admin
from app.admin.utils import create_access_token, verify_password

router = APIRouter()


@router.post("/login")
async def admin_login(
    username: str,
    password: str,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    admin = await db.execute(select(Admin).where(Admin.username == username))
    admin = admin.scalars().first()

    if not admin or not verify_password(password, admin.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": admin.username})
    response.set_cookie(
        key="admin_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"message": "Logged in as admin"}