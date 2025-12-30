from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from jose import JWTError, jwt
from sqlalchemy.future import select
from app.admin.models import Admin
from app.admin.utils import verify_password, create_access_token
from app.database import async_session_maker
from app.config import settings

class AdminAuth(AuthenticationBackend):
    def __init__(self):
        super().__init__(secret_key=settings.SECRET_KEY)

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form["username"], form["password"]

        async with async_session_maker() as db:
            admin = await db.execute(select(Admin).where(Admin.username == username))
            admin = admin.scalars().first()

            if not admin or not verify_password(password, admin.hashed_password):
                return False

            access_token = create_access_token({"sub": admin.username})
            request.session.update({"token": f"Bearer {access_token}"})

        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> RedirectResponse | bool:
        token = request.session.get("token")
        if not token or not token.startswith("Bearer "):
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        try:
            token = token.split(" ")[1]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError:
            return RedirectResponse(request.url_for("admin:login"), status_code=302)

        return True
