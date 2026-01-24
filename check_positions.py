import asyncio
from app.database import async_session_maker
from sqlalchemy import select, func
from app.players.models import Player

async def check():
    async with async_session_maker() as s:
        r = await s.execute(select(Player.position, func.count()).group_by(Player.position))
        for position, count in r.all():
            print(f'{position} - {count}')

asyncio.run(check())
