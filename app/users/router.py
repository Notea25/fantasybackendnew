import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.config import settings
from app.users.dependencies import get_current_user
from app.users.schemas import UserCreateSchema, UserSchema, UserUpdateSchema
from app.users.services import UserService
from app.users.utils import create_access_token, create_refresh_token, verify_token
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
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
        )

        logger.debug(f"User authenticated: {user.id}, tokens issued")
        return {
            "status": "ok",
            "user": UserSchema.model_validate(user),
            "access_token": access_token,
            "refresh_token": refresh_token,
        }
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
        refresh_token = request.cookies.get("refresh_token")
        if not refresh_token:
            logger.debug("No refresh token cookie provided")
            raise AuthenticationFailedException()

        payload = verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            logger.debug("Invalid refresh token payload")
            raise AuthenticationFailedException()

        user_id = payload.get("sub")
        if not user_id:
            logger.debug("No user id in refresh token")
            raise AuthenticationFailedException()

        user = await UserService.get_by_telegram_id(int(user_id))
        if not user:
            logger.debug(f"User not found for refresh token (ID: {user_id})")
            raise AuthenticationFailedException()

        access_token = create_access_token(data={"sub": str(user.id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user.id)})

        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=30 * 24 * 60 * 60,
        )

        return {
            "status": "ok",
            "message": "Token refreshed",
            "access_token": access_token,
            "refresh_token": new_refresh_token,
        }
    except AuthenticationFailedException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during refresh: {str(e)}", exc_info=True)
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