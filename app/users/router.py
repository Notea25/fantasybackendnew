import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.config import settings
from app.users.dependencies import get_current_user
from app.users.schemas import UserCreateSchema, UserSchema, UserUpdateSchema
from app.users.services import UserService
from app.users.utils import create_access_token
from app.utils.exceptions import (
    AuthenticationFailedException,
    InvalidDataException,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.post("/login")
async def login(request: Request, response: Response):
    try:
        logger.debug("Login attempt started")
        user = await get_current_user(request)

        access_token = create_access_token(data={"sub": str(user.id)})

        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        logger.debug(f"User authenticated: {user.id}, token refreshed")
        return {"status": "ok", "user": UserSchema.model_validate(user)}
    except (InvalidDataException, AuthenticationFailedException) as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise AuthenticationFailedException()


@router.get("/protected")
async def protected_route(user: UserSchema = Depends(get_current_user)):
    return {
        "message": f"Hello, {user.username}!",
        "user_id": user.id,
        "authenticated": True,
    }


@router.post("/refresh")
async def refresh(request: Request, response: Response):
    try:
        user = await get_current_user(request)

        access_token = create_access_token(data={"sub": str(user.id)})

        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        return {"status": "ok", "message": "Token refreshed"}
    except Exception:
        raise AuthenticationFailedException()


@router.post("/register")
async def register_user(
    request: Request,
    user_data: UserCreateSchema,
):
    try:
        user_json = await request.json()
        telegram_id = user_json.get("id")
        if not telegram_id:
            raise HTTPException(status_code=400, detail="Telegram ID is required")

        user = await UserService.add_one(user_data=user_data, id=telegram_id)
        return {"status": "ok", "user": UserSchema.model_validate(user)}
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/update")
async def update_user(
    user_id: int,
    user_data: UserUpdateSchema,
    current_user: UserSchema = Depends(get_current_user),
):
    try:
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        user = await UserService.update_user(user_id=user_id, user_data=user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "ok", "user": UserSchema.model_validate(user)}
    except Exception as e:
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")