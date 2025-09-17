# services/index.py
# services/index.py
from datetime import datetime, timedelta

from sqlalchemy import and_, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from src.models.article import Article
from src.models.fixed_material import FixedArticle
from src.models.category import Category            # ← категории

TZ_SHIFT = timedelta(hours=5)

# ─────────────────────────────────────────────────────────────────────────────
#  Вспомогательная функция для выборки по категории / лимиту
# ─────────────────────────────────────────────────────────────────────────────
async def _get_by_category(
    db: AsyncSession,
    base_filters,
    slug: str,
    limit: int,
):
    q = (
        select(Article)
        .join(Article.categories)                 # JOIN news_article_categories
        .filter(base_filters, Category.slug == slug)
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
        .limit(limit)
    )
    return (await db.execute(q)).scalars().all()


async def get_index(db: AsyncSession):
    dt = datetime.now() + TZ_SHIFT
    base_filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
        Article.public_params == 0,
    )

    # ─── 1. Закреплённые (order 1-4) ────────────────────────────────────────
    fixed_q = (
        select(Article)
        .join(FixedArticle, Article.id == FixedArticle.article_id)
        .filter(base_filters, FixedArticle.order <= 4)
        .options(
            selectinload(Article.fixed_article),
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
            ),
        )
        .order_by(FixedArticle.order)
    )
    fixed = (await db.execute(fixed_q)).scalars().all()

    main_article = fixed[0] if fixed else None
    secondary_articles = fixed[1:]
    fixed_ids = [a.id for a in fixed]

    # ─── 2. 20 последних («Последние новости») ─────────────────────────────
    latest_q = (
        select(Article)
        .filter(base_filters)
        .options(
            load_only(
                Article.alias,
                Article.title,
                Article.image,
                Article.published_date,
                Article.description,
                Article.public_types,
            ),
        )
        .order_by(Article.published_date.desc())
        .limit(20)
    )
    latest_articles = (await db.execute(latest_q)).scalars().all()
    for art in latest_articles:
        art.public_type_class = art.public_types[0] if art.public_types else ''

    # ─── 3. Категории для трёх блоков ───────────────────────────────────────
    finance_articles        = await _get_by_category(db, base_filters, "finansy", 4)                          # categoryGrid
    history_articles        = await _get_by_category(db, base_filters, "istorii", 4)                          # historyNews
    tax_reform_articles     = await _get_by_category(db, base_filters, "nalogovaya-reforma-v-kazahstane", 3) # categoryNews
    court_report_articles   = await _get_by_category(db, base_filters, "sudebniy-reportazh", 3)              # courtReport
    explainer_articles      = await _get_by_category(db, base_filters, "pojmyom-chto-k-chemu", 3)            # explainers
    officials_questions     = await _get_by_category(db, base_filters, "voprosy-chinovnikam", 3)             # officialsQuestions
    interview_articles      = await _get_by_category(db, base_filters, "pogovorim-s", 3)                     # interviews
    success_stories         = await _get_by_category(db, base_filters, "sekret-uspeha", 3)                   # successStories

    return {
        # основные блоки
        "main_article": main_article,
        "secondary_articles": secondary_articles,
        "latest_articles": latest_articles,

        # категории
        "finance_articles": finance_articles,                 # для .categoryGrid («Финансы»)
        "history_articles": history_articles,                 # для .historyNews  («Истории»)
        "tax_reform_articles": tax_reform_articles,           # для .categoryNews («Налоговая реформа…»)
        "court_report_articles": court_report_articles,       # для .courtReport («Судебный репортаж»)
        "explainer_articles": explainer_articles,             # для .explainers («Поймём, что к чему»)
        "officials_questions": officials_questions,           # для .officialsQuestions («Вопросы чиновникам»)
        "interview_articles": interview_articles,             # для .interviews («Поговорим с…»)
        "success_stories": success_stories,                   # для .successStories («Секрет успеха»)
    }





async def load_more(db: AsyncSession, page: int = 1):
    """
    «Бесконечный» скролл:
    отдаём закреплённые, начиная с 5-й (order ≥ 5),
    по 9 штук за запрос.
    """
    dt = datetime.now() + TZ_SHIFT
    common_filters = and_(Article.published_date <= dt,
                          Article.article_status == "P")

    per_page = 9
    offset = (page - 1) * per_page

    q = (
        select(Article)
        .join(FixedArticle, Article.id == FixedArticle.article_id)
        .filter(common_filters, Article.public_params == 0,
                FixedArticle.order >= 5)
        .options(
            selectinload(Article.fixed_article),
            load_only(Article.alias, Article.title,
                      Article.image, Article.published_date),
        )
        .order_by(FixedArticle.order)
        .offset(offset)
        .limit(per_page)
    )

    articles = (await db.execute(q)).scalars().all()
    return {"articles": articles}
