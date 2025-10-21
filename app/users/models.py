from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    photo_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    emblem_url: Mapped[Optional[str]] = mapped_column(nullable=True)
    # teams: Mapped[list["Team"]] = relationship(back_populates="user")

    def __repr__(self):
        return self.id
