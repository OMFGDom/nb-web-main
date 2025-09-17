# services/tag.py
from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.models.article import Article
from src.models.tags import Tag
from src.utils.error_handlers import get_object_or_404
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


async def get_tag(
    db: AsyncSession,
    page: int = 1,
    slug: str | None = None,
):
    """
    Лента материалов по тегу.
    """
    tag_q = select(Tag).filter_by(slug=slug)
    tag = await get_object_or_404(query=tag_q, session=db)

    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params.in_([0, 1])  # SQLAlchemy метод, не int
    )

    query = (
        select(Article)
        .filter(filters, Article.tags.any(Tag.slug == slug))
        .options(
            selectinload(Article.tags),
            selectinload(Article.categories),  # <--- это нужно
        )
        .order_by(Article.published_date.desc())
    )

    pagination = Pagination(page=page, per_page=18)
    page_obj = await paginate(db, pagination, query)

    return {"tag": tag, "page": page_obj}
