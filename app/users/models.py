from typing import Optional
from datetime import date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    photo_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    emblem_url: Mapped[Optional[str]] = mapped_column(nullable=True)

    squads: Mapped[list["Squad"]] = relationship(back_populates="user")
    user_leagues: Mapped[list["UserLeague"]] = relationship(back_populates="creator")

    def __repr__(self):
        return f"User {self.username}"
