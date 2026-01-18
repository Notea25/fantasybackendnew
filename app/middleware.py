from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from app.config import settings


async def admin_auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        token = request.cookies.get("admin_token")
        if not token or not token.startswith("Bearer "):
            return JSONResponse(
                status_code=403, content={"detail": "Not authenticated"}
            )

        token = token.split(" ")[1]
        try:
            jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
        except JWTError:
            return JSONResponse(
                status_code=403, content={"detail": "Invalid token"}
            )

    return await call_next(request)