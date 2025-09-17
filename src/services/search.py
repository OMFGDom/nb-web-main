# services/search.py
from datetime import datetime, timedelta

from sqlalchemy import and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.models.article import Article
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


async def search_results(
    db: AsyncSession,
    page_number: int,
    q: str = "",
    sort: str | None = None,
):
    """
    Поиск только по Article.title (иллюстративно; можно добавить full-text).
    """
    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params.in_([0, 1])  # SQLAlchemy метод, не int
    )

    sanitized = f"%{q.lower()}%"
    query = (
        select(Article)
        .options(selectinload(Article.categories))  # <== это добавляет prefetch
        .filter(filters, Article.title.ilike(sanitized))
    )

    query = query.order_by(desc(Article.published_date))

    pagination = Pagination(page=page_number, per_page=6)
    page_obj = await paginate(db, pagination, query)

    return {"q": q, "sort": sort, "page": page_obj, "page_number": page_number}
