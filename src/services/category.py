# services/category.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, load_only

from src.models.article import Article
from src.models.category import Category
from src.utils.error_handlers import get_object_or_404
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


def _last_category_title(art: Article) -> str:
    try:
        return art.categories[-1].title if art.categories else "Новости"
    except Exception:
        return "Новости"


async def get_category(db: AsyncSession, page: int, slug: str) -> Dict[str, Any]:
    """
    Категорийная страница.
    Parent (нет parent_category_id):
      - пагинируем по 24 на страницу (вся страница = 24 элементов),
      - внутри страницы делим:
          featured_top = items[0]
          first_list   = items[1:10]   (9)
          cards_list   = items[10:14]  (4)
          featured_bottom = items[14]
          last_list    = items[15:24]  (9)
    Subcategory (есть parent_category_id):
      - обычная лента по 10.
    """
    # Категория + дети
    category_q = (
        select(Category)
        .filter(Category.slug == slug)
        .options(selectinload(Category.children))
        .limit(1)
    )
    category: Category = await get_object_or_404(query=category_q, session=db)

    is_parent_category: bool = category.parent_category_id is None
    subcategories: List[Category] = (
        [c for c in (category.children or []) if c.is_active] if is_parent_category else []
    )

    # Публикационные фильтры
    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params.in_([0, 1]),
    )

    if is_parent_category:
        # Родитель + дети
        category_ids = [category.id] + [c.id for c in subcategories]

        base_q = (
            select(Article)
            .join(Article.categories)
            .filter(filters, Category.id.in_(category_ids))
            .options(
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

        # Пагинация — строго 24 на страницу (в шаблоне раскладываем)
        pagination = Pagination(page=page, per_page=24)
        page_obj = await paginate(db, pagination, base_q)

        items: List[Article] = page_obj.items or []

        # Бейджи категорий
        for a in items:
            a.badge_category = _last_category_title(a)

        featured_top: Optional[Article] = items[0] if len(items) >= 1 else None
        first_list: List[Article] = items[1:10] if len(items) > 1 else []

        cards_list: List[Article] = items[10:14] if len(items) > 10 else []
        featured_bottom: Optional[Article] = items[14] if len(items) >= 15 else None
        last_list: List[Article] = items[15:24] if len(items) > 15 else []

        return {
            "category": category,
            "is_parent_category": True,
            "subcategories": subcategories,

            # расклад по текущей странице
            "featured_top": featured_top,
            "first_list": first_list,
            "cards_list": cards_list,
            "featured_bottom": featured_bottom,
            "last_list": last_list,

            "page": page_obj,  # для пагинации
        }

    # Subcategory: только текущая категория
    list_q = (
        select(Article)
        .filter(filters, Article.categories.any(Category.slug == slug))
        .options(
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

    pagination = Pagination(page=page, per_page=10)
    page_obj = await paginate(db, pagination, list_q)

    for a in page_obj.items:
        a.badge_category = _last_category_title(a)

    return {
        "category": category,
        "is_parent_category": False,
        "subcategories": [],
        "page": page_obj,
    }
