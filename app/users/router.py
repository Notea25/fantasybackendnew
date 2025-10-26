import logging

from fastapi import APIRouter, Depends, Request, Response

from app.config import settings
from app.exceptions import AuthenticationFailedException, InvalidDataException
from app.users.dependencies import get_current_user
from app.users.schemas import UserSchema
from app.users.services import UserService
from app.users.utils import create_access_token

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
            secure=False,  # В разработке. В продакшене: True
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
async def protected_route(user=Depends(get_current_user)):
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
    except Exception as e:
        raise AuthenticationFailedException()
