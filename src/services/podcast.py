# src/services/podcast.py
import logging
from datetime import datetime, timedelta

from redis.exceptions import RedisError
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only
from sqlalchemy.ext.serializer import loads, dumps

from src.db.database import get_db  # noqa: F401 (для DI-Depends)
from src.grpc.client import user_rpc
from src.models.podcast import Podcast
from src.utils.error_handlers import get_object_or_404

# Тайм-зона проекта (+5 ч. к UTC), как в services/article.py
TZ_SHIFT = timedelta(hours=5)


# --------------------------------------------------------------------------- #
#  Лента подкастов (5 последних опубликованных)
# --------------------------------------------------------------------------- #
async def get_podcasts(db: AsyncSession):
    """
    Возвращает 5 последних подкастов с published_date <= now(+5).
    """
    dt = datetime.now() + TZ_SHIFT
    filters = and_(Podcast.published_date <= dt)

    q = (
        select(Podcast)
        .filter(filters)
        .options(
            load_only(
                Podcast.id,
                Podcast.title,
                Podcast.alias,
                Podcast.image,
                Podcast.published_date,
                Podcast.category_title,
                Podcast.podcast,
            )
        )
        .order_by(Podcast.published_date.desc())
        .limit(5)
    )
    items = (await db.execute(q)).scalars().all()
    return {"podcasts": items}


# --------------------------------------------------------------------------- #
#  Детальная страница подкаста
# --------------------------------------------------------------------------- #
async def podcast_detail(db: AsyncSession, slug: str, curr_redis):
    """
    Детальная по alias. Кеш в Redis (ключ: podcast_{slug}).
    Авторов тянем через user_rpc.user_by_uid по author_ids.
    Похожие — по тому же category_title (до 5 шт, исключая текущий).
    """
    dt = datetime.now() + TZ_SHIFT
    filters = and_(Podcast.published_date <= dt)

    # 1) Пробуем из Redis
    try:
        cached = await curr_redis.get(f"podcast_{slug}")
        if cached:
            podcast: Podcast = loads(cached)
        else:
            raise KeyError
    except Exception:
        query = (
            select(Podcast)
            .filter(filters, Podcast.alias == slug)
        )
        podcast = await get_object_or_404(query=query, session=db)
        try:
            await curr_redis.set(f"podcast_{slug}", dumps(podcast))
        except RedisError as e:
            logging.error(f"Redis SET error: {e}")

    # 2) Авторы
    author_ids = podcast.author_ids or []
    authors = [await user_rpc.user_by_uid(uid=author_id) for author_id in author_ids]
    authors = [a for a in authors if a]

    # 3) Похожие (по category_title)
    related = []
    if podcast.category_title:
        rel_q = (
            select(Podcast)
            .filter(
                filters,
                Podcast.alias != slug,
                Podcast.category_title == podcast.category_title,
            )
            .order_by(Podcast.published_date.desc())
            .limit(5)
        )
        related = (await db.execute(rel_q)).scalars().all()

    next_podcast = None
    prev_podcast = None
    if podcast.published_date:
        # следующий: ближайший позже по дате
        nq = (
            select(Podcast)
            .filter(
                filters,
                Podcast.published_date > podcast.published_date,
            )
            .order_by(Podcast.published_date.asc())
            .limit(1)
        )
        next_podcast = (await db.execute(nq)).scalars().first()

        # предыдущий: ближайший раньше по дате
        pq = (
            select(Podcast)
            .filter(
                filters,
                Podcast.published_date < podcast.published_date,
            )
            .order_by(Podcast.published_date.desc())
            .limit(1)
        )
        prev_podcast = (await db.execute(pq)).scalars().first()

    return {
        "podcast": podcast,
        "related_podcasts": related,
        "authors": authors,
        "next_podcast": next_podcast,
        "prev_podcast": prev_podcast,
    }
