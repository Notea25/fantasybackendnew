from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import DateTime

from app.database import Base


class PlayerStatus(Base):
    __tablename__ = "player_statuses"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status_type: Mapped[str] = mapped_column(nullable=False)  # "red_card", "injured", "left_league"
    tour_start: Mapped[int] = mapped_column(nullable=False)
    tour_end: Mapped[Optional[int]] = mapped_column(nullable=True)  # null = indefinite
    
    player: Mapped["Player"] = relationship(back_populates="statuses")
    
    __table_args__ = (
        Index('ix_player_tours', 'player_id', 'tour_start', 'tour_end'),
    )
    
    def __repr__(self):
        return f"<PlayerStatus {self.player_id} {self.status_type} tours {self.tour_start}-{self.tour_end}>"