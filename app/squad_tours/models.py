from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table, func, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.player_match_stats.models import PlayerMatchStats


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


class SquadTour(Base):
    __tablename__ = "squad_tours"
    id: Mapped[int] = mapped_column(primary_key=True)
    squad_id: Mapped[int] = mapped_column(
        ForeignKey("squads.id", ondelete="CASCADE"),
        nullable=False,
    )
    tour_id: Mapped[int] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"))
    is_current: Mapped[bool] = mapped_column(default=False)
    used_boost: Mapped[Optional[str]] = mapped_column(nullable=True)
    points: Mapped[int] = mapped_column(default=0)
    penalty_points: Mapped[int] = mapped_column(default=0)
    captain_id: Mapped[Optional[int]] = mapped_column(ForeignKey("players.id"), nullable=True)
    vice_captain_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"), nullable=True
    )
    
    # State fields moved from Squad
    budget: Mapped[int] = mapped_column(default=100_000)
    replacements: Mapped[int] = mapped_column(default=2)
    is_finalized: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    squad: Mapped["Squad"] = relationship(back_populates="tour_history")
    tour: Mapped["Tour"] = relationship(back_populates="squads")
    main_players: Mapped[List["Player"]] = relationship(
        secondary=squad_tour_players, back_populates="squad_tours", lazy="selectin"
    )
    bench_players: Mapped[List["Player"]] = relationship(
        secondary=squad_tour_bench_players, back_populates="bench_squad_tours", lazy="selectin"
    )

    @property
    def main_player_ids(self) -> List[int]:
        return [player.id for player in self.main_players]

    @property
    def bench_player_ids(self) -> List[int]:
        return [player.id for player in self.bench_players]

    def calculate_players_cost(self) -> int:
        return sum(p.market_value for p in self.main_players) + sum(
            p.market_value for p in self.bench_players
        )

    def validate_players(
        self, main_players: List["Player"], bench_players: List["Player"]
    ) -> None:
        if len(main_players) != 11:
            raise ValueError("Main squad must have exactly 11 players")
        if len(bench_players) != 4:
            raise ValueError("Bench must have exactly 4 players")

        # Check that main squad has at least 1 player of each position
        main_position_counts = {}
        for player in main_players:
            position = player.position
            main_position_counts[position] = main_position_counts.get(position, 0) + 1
        
        # Required: at least 1 Goalkeeper, 1 Defender, 1 Midfielder, 1 Attacker
        if main_position_counts.get("Goalkeeper", 0) < 1:
            raise ValueError("Main squad must have at least 1 Goalkeeper")
        if main_position_counts.get("Defender", 0) < 1:
            raise ValueError("Main squad must have at least 1 Defender")
        if main_position_counts.get("Midfielder", 0) < 1:
            raise ValueError("Main squad must have at least 1 Midfielder")
        if main_position_counts.get("Attacker", 0) < 1 and main_position_counts.get("Forward", 0) < 1:
            raise ValueError("Main squad must have at least 1 Attacker or Forward")

        total_cost = sum(p.market_value for p in main_players + bench_players)
        if total_cost > self.budget:
            raise ValueError("Total players cost exceeds squad budget")

        # Get league_id from Squad relationship
        league_id = self.squad.league_id
        for player in main_players + bench_players:
            if player.league_id != league_id:
                raise ValueError("All players must be from the same league")

        club_counts = {}
        for player in main_players + bench_players:
            club_counts[player.team_id] = club_counts.get(player.team_id, 0) + 1
            if club_counts[player.team_id] > 3:
                raise ValueError(
                    "Cannot have more than 3 players from the same club"
                )

    def count_different_players(
        self, new_main_ids: List[int], new_bench_ids: List[int]
    ) -> int:
        current_main_ids = {p.id for p in self.main_players}
        current_bench_ids = {p.id for p in self.bench_players}
        return len(current_main_ids - set(new_main_ids)) + len(
            current_bench_ids - set(new_bench_ids)
        )

    async def calculate_points(self, session) -> int:
        total_points = 0

        for player in self.main_players:
            player_points_stmt = (
                select(func.sum(PlayerMatchStats.points))
                .where(PlayerMatchStats.player_id == player.id)
            )
            player_points_result = await session.execute(player_points_stmt)
            player_points = player_points_result.scalar() or 0
            total_points += player_points

        for player in self.bench_players:
            player_points_stmt = (
                select(func.sum(PlayerMatchStats.points))
                .where(PlayerMatchStats.player_id == player.id)
            )
            player_points_result = await session.execute(player_points_stmt)
            player_points = player_points_result.scalar() or 0
            total_points += player_points

        return total_points
