from sqlalchemy import select


from app.database import async_session_maker
from app.exceptions import ResourceNotFoundException


class BaseService:
    model = None

    @classmethod
    async def _get_session(cls):
        async with async_session_maker() as session:
            return session

    @classmethod
    async def find_all(cls):
        async with await cls._get_session() as session:
            query = select(cls.model)
            res = await session.execute(query)
            return res.scalars().all()

    @classmethod
    async def find_filtered(cls, **filter_by):
        async with await cls._get_session() as session:
            query = select(cls.model).filter_by(**filter_by)
            res = await session.execute(query)
            return res.scalars().all()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with await cls._get_session() as session:
            query = select(cls.model).filter_by(**filter_by)
            res = await session.execute(query)
            return res.scalar_one_or_none()

    @classmethod
    async def add_one(cls, **data):
        async with await cls._get_session() as session:
            instance = cls.model(**data)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @classmethod
    async def delete(cls, **filter_by):
        async with await cls._get_session() as session:
            instance = await cls.find_one_or_none(**filter_by)
            if not instance:
                raise ResourceNotFoundException()

            await session.delete(instance)
            await session.commit()

    @classmethod
    async def update(cls, model_id: int, **model_data):
        async with await cls._get_session() as session:
            instance = await cls.find_one_or_none(id=model_id)
            if not instance:
                raise ResourceNotFoundException()

            for key, value in model_data.items():
                setattr(instance, key, value)

            await session.commit()
            await session.refresh(instance)
            return instance
