from sqladmin import ModelView

from app.boards.models import Boards
from app.cards.models import Cards
from app.users.models import Users
from app.lists.models import Lists
from app.spaces.models import Spaces
from app.backgrounds.models import Backgrounds
from app.users.password_reset.models import Reset
from app.users.verification.models import Verification


class BoardsAdmin(ModelView, model=Boards):
    column_list = "__all__"
    name = "Board"
    name_plural = "Boards"
    icon = "fa-solid fa-chess-board"


class CardsAdmin(ModelView, model=Cards):
    column_list = "__all__"
    name = "Cards"
    name_plural = "Cards"
    icon = "fa-solid fa-credit-card"


class UsersAdmin(ModelView, model=Users):
    column_list = [Users.id, Users.email]
    can_delete = False
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-user"
    column_details_exclude_list = [Users.hashed_password]


class ListsAdmin(ModelView, model=Lists):
    column_list = "__all__"
    name = "List"
    name_plural = "Lists"
    icon = "fa-solid fa-list"


class SpacesAdmin(ModelView, model=Spaces):
    column_list = "__all__"
    name = "Space"
    name_plural = "Spaces"
    icon = "fa-solid fa-rocket"


class BackgroundsAdmin(ModelView, model=Backgrounds):
    column_list = "__all__"
    name = "Background"
    name_plural = "Backgrounds"
    icon = "fa-solid fa-burger"


class VerificationAdmin(ModelView, model=Verification):
    column_list = "__all__"
    name = "Verification"
    name_plural = "Verification"
    icon = "fa-solid fa-check"

class ResetAdmin(ModelView, model=Reset):
    column_list = "__all__"
    name = "Reset"
    name_plural = "Reset"
    icon = "fa-solid fa-power-off"

