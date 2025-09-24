# services/index.py
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import asyncio
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from src.models.article import Article
from src.models.fixed_material import FixedArticle
from src.models.category import Category
from src.models.podcast import Podcast  # ← добавили
from src.grpc.client import user_rpc

# Asia/Almaty (UTC+5)
TZ_SHIFT = timedelta(hours=5)


# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные
# ─────────────────────────────────────────────────────────────────────────────
async def _get_by_category(
    db: AsyncSession,
    base_filters,
    slug: str,
    limit: int,
) -> List[Article]:
    q = (
        select(Article)
        .join(Article.categories)
        .filter(base_filters, Category.slug == slug)
        .options(
            selectinload(Article.categories),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
                Article.author_ids,
                Article.quote,
            ),
        )
        .order_by(Article.published_date.desc())
        .limit(limit)
    )
    return (await db.execute(q)).scalars().all()


def _last_category_title(art: Article) -> str:
    try:
        return art.categories[-1].title if art.categories else "Новости"
    except Exception:
        return "Новости"


def _map_author_for_template(user: Dict[str, Any]) -> Dict[str, Any]:
    image = user.get("image") or {}
    return {
        "firstName": user.get("firstName", ""),
        "lastName": user.get("lastName", ""),
        "image": {
            "image_200_webp": image.get("image_200_webp") or image.get("image_webp_200"),
            "image_webp_200": image.get("image_webp_200") or image.get("image_200_webp"),
            "alt": image.get("alt", ""),
        },
    }


async def _hydrate_first_authors(articles: List[Article]) -> None:
    ids: List[str] = []
    for a in articles:
        author_ids = getattr(a, "author_ids", None)
        if author_ids:
            fid = author_ids[0]
            if fid:
                ids.append(fid)

    unique_ids = list({i for i in ids if i})
    if not unique_ids or not hasattr(user_rpc, "user_by_uid"):
        return

    async def fetch(uid: str):
        try:
            return await user_rpc.user_by_uid(uid=uid)
        except Exception:
            return None

    results = await asyncio.gather(*(fetch(uid) for uid in unique_ids), return_exceptions=False)

    authors_map: Dict[str, Dict[str, Any]] = {}
    for u in results:
        if isinstance(u, dict):
            uid = u.get("id")
            if uid:
                authors_map[uid] = u

    for a in articles:
        fa = None
        author_ids = getattr(a, "author_ids", None)
        if author_ids:
            u = authors_map.get(author_ids[0])
            if u:
                fa = _map_author_for_template(u)
        setattr(a, "first_author", fa)


async def _get_section_block(
    db: AsyncSession,
    base_filters,
    parent_slug: str,
    total_limit: int,
    with_featured: bool = True,
) -> Dict[str, Any]:
    """
    Возвращает блок: родительскую категорию, её детей, и последние статьи по ним.
    - with_featured=True: 1 большая + остальной список
    - with_featured=False: вся выборка в items, featured=None
    """
    parent_q = (
        select(Category)
        .filter(Category.slug == parent_slug, Category.is_active.is_(True))
        .options(selectinload(Category.children))
        .limit(1)
    )
    parent: Optional[Category] = (await db.execute(parent_q)).scalar_one_or_none()
    if not parent:
        return {"featured": None, "items": [], "parent": None, "subcats": []}

    subcats: List[Category] = [c for c in (parent.children or []) if c.is_active]
    category_ids = [parent.id] + [c.id for c in subcats]

    arts_q = (
        select(Article)
        .join(Article.categories)
        .filter(base_filters, Category.id.in_(category_ids))
        .options(
            selectinload(Article.categories),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
                Article.author_ids,
                Article.quote,
            ),
        )
        .order_by(Article.published_date.desc())
        .limit(total_limit)
    )
    arts: List[Article] = (await db.execute(arts_q)).scalars().all()

    for art in arts:
        art.badge_category = _last_category_title(art)

    if with_featured and arts:
        featured = arts[0]
        items = arts[1:]
    else:
        featured = None
        items = arts

    return {"featured": featured, "items": items, "parent": parent, "subcats": subcats}


# ─────────────────────────────────────────────────────────────────────────────
# Главная страница
# ─────────────────────────────────────────────────────────────────────────────
async def get_index(db: AsyncSession) -> Dict[str, Any]:
    dt = datetime.now() + TZ_SHIFT
    base_filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params == 0,
    )

    # 1) Закреплённые (order 1–6)
    fixed_q = (
        select(Article)
        .join(FixedArticle, Article.id == FixedArticle.article_id)
        .filter(base_filters, FixedArticle.order <= 6)
        .options(
            selectinload(Article.fixed_article),
            selectinload(Article.categories),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
                Article.author_ids,
            ),
        )
        .order_by(FixedArticle.order)
    )
    fixed = (await db.execute(fixed_q)).scalars().all()

    main_article: Optional[Article] = fixed[0] if fixed else None
    secondary_articles: List[Article] = fixed[1:3]  # 2–3
    third_articles: List[Article] = fixed[3:6]      # 4–6

    if main_article:
        main_article.badge_category = _last_category_title(main_article)
    for art in secondary_articles:
        art.badge_category = _last_category_title(art)
    for art in third_articles:
        art.badge_category = _last_category_title(art)

    # 2) Последние 20
    latest_q = (
        select(Article)
        .filter(base_filters)
        .options(
            selectinload(Article.categories),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
                Article.public_types,
                Article.author_ids,
            ),
        )
        .order_by(Article.published_date.desc())
        .limit(20)
    )
    latest_articles = (await db.execute(latest_q)).scalars().all()
    for art in latest_articles:
        art.public_type_class = art.public_types[0] if art.public_types else ""

    # 3) Интервью (1 шт. + автор)
    interview_articles = await _get_by_category(db, base_filters, "intervyu", 1)
    await _hydrate_first_authors(interview_articles)

    # 4) Экономика (1 featured + 6)
    economy = await _get_section_block(db, base_filters, parent_slug="ekonomika", total_limit=7, with_featured=True)

    # 5) Геополитика (1 featured + 4 для грида)
    geopolitics = await _get_section_block(db, base_filters, parent_slug="geopolitika", total_limit=5, with_featured=True)

    # 6) Исследования (1 featured + 6)
    research = await _get_section_block(db, base_filters, parent_slug="issledovaniya", total_limit=7, with_featured=True)

    # 7) Life style (только грид из 4)
    lifestyle = await _get_section_block(db, base_filters, parent_slug="life-style", total_limit=4, with_featured=False)

    # 8) МНЕНИЕ (1 шт. + автор) — для блока в сайдбаре
    opinion_articles = await _get_by_category(db, base_filters, "mnenie", 1)
    await _hydrate_first_authors(opinion_articles)

    # 9) Элементы для мини-секции колонок
    editor_focus_article = latest_articles[0] if latest_articles else None
    opinion_article = opinion_articles[0] if opinion_articles else None
    interview_article = interview_articles[0] if interview_articles else None

    # 10) Подкасты (4 последних)
    podcasts_q = (
        select(Podcast)
        .filter(Podcast.published_date <= dt)
        .options(
            load_only(
                Podcast.alias,
                Podcast.title,
                Podcast.image,
                Podcast.podcast,
                Podcast.published_date,
                Podcast.category_title,
            )
        )
        .order_by(Podcast.published_date.desc())
        .limit(4)
    )
    latest_podcasts: List[Podcast] = (await db.execute(podcasts_q)).scalars().all()

    return {
        # основные блоки
        "main_article": main_article,
        "secondary_articles": secondary_articles,
        "third_articles": third_articles,
        "latest_articles": latest_articles,

        # интервью
        "interview_articles": interview_articles,

        # экономика
        "economy_featured": economy["featured"],
        "economy_articles": economy["items"],
        "economy_parent": economy["parent"],
        "economy_subcategories": economy["subcats"],

        # геополитика
        "geopolitics_featured": geopolitics["featured"],
        "geopolitics_articles": geopolitics["items"],
        "geopolitics_parent": geopolitics["parent"],
        "geopolitics_subcategories": geopolitics["subcats"],

        # исследования
        "research_featured": research["featured"],
        "research_articles": research["items"],
        "research_parent": research["parent"],
        "research_subcategories": research["subcats"],

        # life style
        "lifestyle_articles": lifestyle["items"],
        "lifestyle_parent": lifestyle["parent"],
        "lifestyle_subcategories": lifestyle["subcats"],

        # мини-секция (фокус редактора / мнение / интервью)
        "editor_focus_article": editor_focus_article,
        "opinion_article": opinion_article,
        "interview_article": interview_article,

        # подкасты (для блока на главной)
        "latest_podcasts": latest_podcasts,
    }
