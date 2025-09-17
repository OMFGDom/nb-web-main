from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload
from src.db.database import get_db
from src.models.article import Article
from src.utils.pagination import paginate, Pagination


async def get_articles_404(db: AsyncSession):
    dt = datetime.now() + timedelta(hours=5)
    filters = and_(
        Article.published_date <= dt,
        # Article.status == "P"
        Article.article_status == "P"
    )
    articles_result = await db.execute(
        select(Article)
        .filter(filters)
        .options(selectinload(Article.categories))
        .order_by(Article.published_date.desc())
        .limit(6)
    )
    articles = articles_result.scalars().all()


    context = {"articles": articles}
    return context


