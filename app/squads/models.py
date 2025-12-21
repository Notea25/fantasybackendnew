from sqlalchemy import Column, ForeignKey, Table, Integer, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum

# Ассоциативные таблицы для текущих составов
squad_players_association = Table(
    "squad_players_association",
    Base.metadata,
    Column("squad_id", ForeignKey("squads.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

squad_bench_players_association = Table(
    "squad_bench_players_association",
    Base.metadata,
    Column("squad_id", ForeignKey("squads.id"), primary_key=True),
    Column("player_id", ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

# Ассоциативные таблицы для истории составов
squad_tour_players = Table(
    "squad_tour_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
)

squad_tour_bench_players = Table(
    "squad_tour_bench_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
)

class BoostType(PyEnum):
    BENCH_BOOST = "bench_boost"
    TRIPLE_CAPTAIN = "triple_captain"
    TRANSFERS_PLUS = "transfers_plus"
    GOLD_TOUR = "gold_tour"
    DOUBLE_BET = "double_bet"

class Squad(Base):
    __tablename__ = "squads"
    __table_args__ = (
        UniqueConstraint('user_id', 'league_id', name='unique_squad_per_league_per_user'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    fav_team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    budget: Mapped[int] = mapped_column(default=100_000)
    replacements: Mapped[int] = mapped_column(default=3)
    league_id: Mapped[int] = mapped_column(ForeignKey("leagues.id"), nullable=False)
    points: Mapped[int] = mapped_column(default=0)

    # Текущий тур
    current_tour_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tours.id"), nullable=True)

    # Бусты
    available_boosts: Mapped[int] = mapped_column(default=5)

    # Отношения
    user: Mapped["User"] = relationship(back_populates="squads")
    league: Mapped["League"] = relationship(back_populates="squads")
    current_main_players: Mapped[list["Player"]] = relationship(
        secondary=squad_players_association, back_populates="main_squads"
    )
    current_bench_players: Mapped[list["Player"]] = relationship(
        secondary=squad_bench_players_association, back_populates="bench_squads"
    )

    # История туров
    tour_history: Mapped[list["SquadTour"]] = relationship(back_populates="squad")
    used_boosts: Mapped[list["Boost"]] = relationship(back_populates="squad")

    def calculate_points(self):
        main_points = sum(player.points for player in self.current_main_players)
        bench_points = sum(player.points for player in self.current_bench_players) / 2
        return int(main_points + bench_points)

    def __repr__(self):
        return f"{self.name} (User: {self.user_id})"

    def get_boosts_info(self):
        """Возвращает информацию о бустах для отображения в админке"""
        return [
            {
                'type': boost.type.value,
                'tour_id': boost.tour_id,
                'used_at': boost.used_at
            }
            for boost in self.used_boosts
        ]

class SquadTour(Base):
    __tablename__ = "squad_tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"))
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"))
    is_current: Mapped[bool] = mapped_column(default=False)
    used_boost: Mapped[Optional[BoostType]] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(default=0)

    # Отношения
    squad: Mapped["Squad"] = relationship(back_populates="tour_history")
    tour: Mapped["Tour"] = relationship(back_populates="squads")
    main_players: Mapped[list["Player"]] = relationship(
        secondary=squad_tour_players, back_populates="squad_tours"
    )
    bench_players: Mapped[list["Player"]] = relationship(
        secondary=squad_tour_bench_players, back_populates="squad_tours"
    )

class Boost(Base):
    __tablename__ = "boosts"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id"))
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"))
    type: Mapped[BoostType]
    used_at: Mapped[datetime] = mapped_column(default=datetime.now)

    squad: Mapped["Squad"] = relationship(back_populates="used_boosts")

    def __repr__(self):
        return f"{self.type.value} for squad {self.squad_id} in tour {self.tour_id}"