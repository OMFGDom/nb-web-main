# services/author.py
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.grpc.client import user_rpc
from src.models.article import Article
from src.utils.pagination import paginate, Pagination

TZ_SHIFT = timedelta(hours=5)


async def get_authors(db: AsyncSession, page: int, q: str = ""):
    authors_data = await user_rpc.get_users(page=page)
    print(authors_data)
    authors = authors_data.get('users', []) if authors_data else []
    query = q.lower().strip()

    # фильтрация по is_active и is_display
    # authors = [
    #     user for user in authors
    #     if user.get('is_active') is True and user.get('is_display') is True
    # ]

    if query:
        filtered_authors = []
        for user in authors:
            first_name = user.get('firstName', '').lower().strip()
            last_name = user.get('lastName', '').lower().strip()
            full_name_1 = f"{first_name} {last_name}"
            full_name_2 = f"{last_name} {first_name}"
            if query in full_name_1 or query in full_name_2:
                filtered_authors.append(user)
        authors = filtered_authors

    total_users = authors_data.get('totalUsers', 0)
    pages = total_users // 20 + (1 if total_users % 10 else 0)

    return {"authors": authors, "page": page, "pages": pages}


async def author_detail(db: AsyncSession, page: int = 1, uid: str = ""):
    dt = datetime.now() + TZ_SHIFT

    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P"
    )

    author = await user_rpc.user_by_uid(uid=uid)
    if not author:
        raise HTTPException(status_code=404, detail="Not Found")

    query = (
        select(Article)
        .options(selectinload(Article.categories))  # <-- ЭТО НУЖНО
        .filter(filters, Article.author_ids.contains([author.get("id", "")]))
        .order_by(Article.published_date.desc())
    )

    page_size = 10
    pagination = Pagination(page=page, per_page=page_size)
    page = await paginate(db, pagination, query)

    context = {
        "author": author,
        "page": page,
        "content_type": "articles"
    }

    return context

async def api_author():
    authors = await user_rpc.get_users()
    authors = authors if authors else {}
    context = authors.get('users', [])

    return context