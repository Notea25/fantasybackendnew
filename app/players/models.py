from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Player(Base):
    __tablename__ = "players"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]
    number: Mapped[int] = mapped_column(nullable=True)
    position: Mapped[str] = mapped_column(nullable=True)
    photo: Mapped[str] = mapped_column(nullable=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    market_value: Mapped[int] = mapped_column(nullable=True)
    sport: Mapped[int] = mapped_column(default=1)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    team: Mapped["Team"] = relationship(back_populates="players")
    league: Mapped["League"] = relationship(back_populates="players")
    stats: Mapped[list["PlayerStats"]] = relationship(back_populates="player", lazy="selectin")
    main_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_players_association", back_populates="players"
    )
    bench_squads: Mapped[list["Squad"]] = relationship(
        secondary="squad_bench_players_association", back_populates="bench_players"
    )

    @property
    def points(self) -> int:
        if self.stats:
            # Возвращаем очки из последней статистики игрока
            return self.stats[-1].points if self.stats else 0
        return 0

    def __repr__(self):
        return self.name
