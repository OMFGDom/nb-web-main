from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.database import get_db
from src.models.article import Article


async def get_about(db: AsyncSession):
    dt = datetime.now() + timedelta(hours=5)
    filters = (
            (Article.published_date <= dt)
    )

    context = {}
    return context


async def get_security(db: AsyncSession):
    dt = datetime.now() + timedelta(hours=5)
    filters = (
            (Article.published_date <= dt)
    )

    context = {}
    return context
