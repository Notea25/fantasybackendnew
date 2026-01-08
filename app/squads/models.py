from typing import Optional
from sqlalchemy import Column, ForeignKey, Table, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.custom_leagues.models import custom_league_squads

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
    extend_existing=True,
)

squad_tour_bench_players = Table(
    "squad_tour_bench_players",
    Base.metadata,
    Column("squad_tour_id", Integer, ForeignKey("squad_tours.id"), primary_key=True),
    Column("player_id", Integer, ForeignKey("players.id"), primary_key=True),
    extend_existing=True,
)

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
    available_boosts: Mapped[int] = mapped_column(default=5)
    current_tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"), nullable=True)

    # Отношения
    user: Mapped["User"] = relationship(back_populates="squads")
    league: Mapped["League"] = relationship(back_populates="squads")
    current_main_players: Mapped[list["Player"]] = relationship(
        secondary=squad_players_association,
        back_populates="main_squads"
    )
    current_bench_players: Mapped[list["Player"]] = relationship(
        secondary=squad_bench_players_association,
        back_populates="bench_squads"
    )

    # История туров
    tour_history: Mapped[list["SquadTour"]] = relationship(back_populates="squad")
    used_boosts: Mapped[list["Boost"]] = relationship(back_populates="squad")
    custom_leagues: Mapped[list["CustomLeague"]] = relationship(
        secondary=custom_league_squads, back_populates="squads"
    )

    def calculate_players_cost(self):
        """Рассчитывает общую стоимость игроков в скваде"""
        return sum(p.market_value for p in self.current_main_players) + \
               sum(p.market_value for p in self.current_bench_players)

    def validate_players(self, main_players, bench_players):
        """Валидация игроков по всем правилам"""
        if len(main_players) != 11:
            raise ValueError("Main squad must have exactly 11 players")
        if len(bench_players) != 4:
            raise ValueError("Bench must have exactly 4 players")

        total_cost = sum(p.market_value for p in main_players + bench_players)
        if total_cost > self.budget:
            raise ValueError("Total players cost exceeds squad budget")

        for player in main_players + bench_players:
            if player.league_id != self.league_id:
                raise ValueError("All players must be from the same league")

        club_counts = {}
        for player in main_players + bench_players:
            club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
            if club_counts[player.team_id] > 3:
                raise ValueError("Cannot have more than 3 players from the same club")

    def count_different_players(self, new_main_ids, new_bench_ids):
        """Считает количество отличающихся игроков"""
        current_main_ids = {p.id for p in self.current_main_players}
        current_bench_ids = {p.id for p in self.current_bench_players}
        return len(current_main_ids - set(new_main_ids)) + \
               len(current_bench_ids - set(new_bench_ids))

    def __repr__(self):
        return f"{self.name} (User: {self.user_id})"


class SquadTour(Base):
    __tablename__ = "squad_tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(ForeignKey("squads.id", ondelete="CASCADE"))
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id"))
    is_current: Mapped[bool] = mapped_column(default=False)
    used_boost: Mapped[Optional[str]] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(default=0)

    # Отношения
    squad: Mapped["Squad"] = relationship(back_populates="tour_history")
    tour: Mapped["Tour"] = relationship(back_populates="squads")
    main_players: Mapped[list["Player"]] = relationship(
        secondary=squad_tour_players,
        back_populates="squad_tours"
    )
    bench_players: Mapped[list["Player"]] = relationship(
        secondary=squad_tour_bench_players,
        back_populates="bench_squad_tours"
    )

    def __repr__(self):
        return f"Squad {self.squad_id} Tour {self.tour_id}"
