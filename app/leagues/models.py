from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.config import settings

from app.database import Base


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    sport: Mapped[int] = mapped_column(default=settings.FOOTBALL_SPORT_ID)

    matches: Mapped[list["Match"]] = relationship(back_populates="league")

    def __repr__(self):
        return self.name

