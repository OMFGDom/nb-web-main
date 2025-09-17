# services/category.py
from datetime import datetime, timedelta

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from src.models.article import Article
from src.models.category import Category
from src.utils.error_handlers import get_object_or_404
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


async def get_category(db: AsyncSession, page: int, slug: str):
    """
    Лента материалов по категории (slug).
    """
    category_q = select(Category).filter_by(slug=slug)
    category = await get_object_or_404(query=category_q, session=db)

    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params.in_([0, 1])  # SQLAlchemy метод, не int
    )

    query = (
        select(Article)
        .filter(filters, Article.categories.any(Category.slug == slug))
        .options(selectinload(Article.categories))
        .order_by(Article.published_date.desc())
    )

    pagination = Pagination(page=page, per_page=10)
    page_obj = await paginate(db, pagination, query)

    return {"category": category, "page": page_obj}
