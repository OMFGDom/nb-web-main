# services/base.py
from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only

from src.models.article import Article
from src.models.fixed_material import FixedArticle
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


async def get_base(db: AsyncSession, title: str = "", year: str = "2025"):
    """
    Данные для базового шаблона (хедер/футер/сайдбар и т. п.).
    """
    dt = datetime.now() + TZ_SHIFT
    filters = and_(Article.published_date <= dt, Article.article_status == "P")

    # ── 1. Закреплённые статьи (FixedArticle) ────────────────────────────────
    fixed_q = (
        select(Article)
        .join(FixedArticle, Article.id == FixedArticle.article_id)
        .filter(filters)
        .options(load_only(Article.alias, Article.title,
                           Article.image, Article.published_date))
        .order_by(FixedArticle.order)
        .limit(5)
    )
    fixed_articles = (await db.execute(fixed_q)).scalars().all()

    # ── 2. Последние 6 обычных статей ────────────────────────────────────────
    latest_q = (
        select(Article)
        .filter(filters)
        .options(load_only(Article.alias, Article.title,
                           Article.image, Article.published_date))
        .order_by(Article.published_date.desc())
        .limit(6)
    )
    latest_articles = (await db.execute(latest_q)).scalars().all()

    prev_year = str(int(year) - 1)
    prev_prev_year = str(int(year) - 2)

    return {
        "title": title,
        "fixed_articles": fixed_articles,
        "latest_articles": latest_articles,
        "year": year,
        "prev_year": prev_year,
        "prev_prev_year": prev_prev_year,
    }
