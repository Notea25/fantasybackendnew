from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class League(Base):
    __tablename__ = "leagues"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    logo: Mapped[str] = mapped_column(nullable=True)
    country: Mapped[str] = mapped_column(nullable=True)
    sport: Mapped[str] = mapped_column(default='football')

    matches: Mapped[list["Match"]] = relationship(back_populates="league")
    squads: Mapped[list["Squad"]] = relationship(back_populates="league")
    players: Mapped[list["Player"]] = relationship(back_populates="league")
    teams: Mapped[list["Team"]] = relationship(back_populates="league")
    tours: Mapped[list["Tour"]] = relationship(back_populates="league")
    custom_leagues: Mapped[list["CustomLeague"]] = relationship(back_populates="league")
