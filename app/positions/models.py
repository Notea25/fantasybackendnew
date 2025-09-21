from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SportType(Base):
    __tablename__ = "sport_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    players: Mapped[list["Player"]] = relationship(back_populates="sport_type")

    def __repr__(self):
        return f"<SportType(name='{self.name}')>"

class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    def __repr__(self):
        return f"<Position(name='{self.name}')>"

    players: Mapped[list["Player"]] = relationship(back_populates="position")