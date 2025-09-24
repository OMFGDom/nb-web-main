# services/tag.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, load_only

from src.models.article import Article
from src.models.tags import Tag
from src.models.category import Category
from src.utils.error_handlers import get_object_or_404
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


def _last_category_title(art: Article) -> str:
    try:
        return art.categories[-1].title if art.categories else "Новости"
    except Exception:
        return "Новости"


async def get_tag(
    db: AsyncSession,
    page: int = 1,
    slug: str | None = None,
) -> Dict[str, Any]:
    """
    Лента материалов по тегу.
    Страница: 18 материалов на страницу (как у вас и было).
    """
    tag_q = select(Tag).filter_by(slug=slug)
    tag = await get_object_or_404(query=tag_q, session=db)

    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params.in_([0, 1]),
    )

    query = (
        select(Article)
        .filter(filters, Article.tags.any(Tag.slug == slug))
        .options(
            selectinload(Article.tags),
            selectinload(Article.categories),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
            ),
        )
        .order_by(Article.published_date.desc())
    )

    pagination = Pagination(page=page, per_page=18)
    page_obj = await paginate(db, pagination, query)

    # предвычислим бейдж категории (на будущее; в шаблоне можно не использовать)
    for a in page_obj.items:
        a.badge_category = _last_category_title(a)

    return {"tag": tag, "page": page_obj}
