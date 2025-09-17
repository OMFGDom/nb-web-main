# services/article.py
import logging
import re
from datetime import datetime, timedelta
from urllib import parse

from redis.exceptions import RedisError
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload
from sqlalchemy.ext.serializer import loads, dumps

from src.db.database import get_db  # noqa: F401 (for DI-Depends)
from src.grpc.client import user_rpc
from src.models.article import Article, article_category
from src.models.category import Category
from src.models.fixed_material import FixedArticle  # noqa: F401 (используется через relationship)
from src.utils.error_handlers import get_object_or_404
from src.utils.pagination import paginate, Pagination

# Тайм-зона проекта (+5 ч. к UTC)
TZ_SHIFT = timedelta(hours=5)


# --------------------------------------------------------------------------- #
#  Анонс-лента (5 последних опубликованных статей)
# --------------------------------------------------------------------------- #
async def get_articles(db: AsyncSession):
    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P",
    )
    q = (
        select(Article)
        .filter(filters)
        .options(load_only(Article.id, Article.title, Article.alias,
                           Article.image, Article.published_date))
        .order_by(Article.published_date.desc())
        .limit(5)
    )
    articles = (await db.execute(q)).scalars().all()
    return {"articles": articles}


# --------------------------------------------------------------------------- #
#  Детальная страница
# --------------------------------------------------------------------------- #
async def article_detail(db: AsyncSession, slug: str, curr_redis):
    dt = datetime.now() + TZ_SHIFT
    filters = and_(Article.article_status == "P", Article.published_date <= dt)

    # ── 1. Пытаемся вытащить из Redis ─────────────────────────────────────────
    try:
        cached = await curr_redis.get(f"article_{slug}")
        if cached:
            article: Article = loads(cached)
        else:
            raise KeyError
    except Exception:
        query = (
            select(Article)
            .filter(filters, Article.alias == slug)
            .options(selectinload(Article.categories), selectinload(Article.tags))
        )
        article = await get_object_or_404(query=query, session=db)
        try:
            await curr_redis.set(f"article_{slug}", dumps(article))
        except RedisError as e:
            logging.error(f"Redis SET error: {e}")

    author_ids = article.author_ids or []
    authors = [await user_rpc.user_by_uid(uid=author_id) for author_id in author_ids]
    authors = [author for author in authors if author]

    # ── 3. Похожие статьи (по категориям) ─────────────────────────────────────
    category_ids = [cat.id for cat in article.categories]


    related_q = (
        select(Article)
        .distinct(Article.id, Article.published_date)
        .join(article_category).join(Category)
        .filter(
            filters,
            Article.alias != slug,
            Category.id.in_(category_ids),
        )
        .order_by(Article.published_date.desc())
        .limit(5)
    )
    related_articles = (await db.execute(related_q)).scalars().all()

    return {
        "article": article,
        "related_articles": related_articles,
        "authors": authors,
    }


# --------------------------------------------------------------------------- #
#  Предпросмотр (статья в статусе != R)
# --------------------------------------------------------------------------- #
async def article_preview(db: AsyncSession, uid: str):
    dt = datetime.now() + TZ_SHIFT
    query = (
        select(Article)
        .filter(Article.id == uid, Article.article_status != "R")
        .options(selectinload(Article.categories), selectinload(Article.tags))
    )
    article = await get_object_or_404(query=query, session=db)

    author_ids = article.author_ids or []
    authors = [await user_rpc.user_by_uid(uid=author_id) for author_id in author_ids]
    authors = [author for author in authors if author]

    category_ids = [cat.id for cat in article.categories]
    filters = and_(Article.published_date <= dt, Article.article_status == "P")

    related_q = (
        select(Article)
        .join(article_category).join(Category)
        .filter(filters, Article.id != uid, Category.id.in_(category_ids))
        .order_by(Article.published_date.desc())
        .limit(5)
    )
    related_articles = (await db.execute(related_q)).scalars().all()

    # 5 самых свежих статей (без EditorChoice/PopularArticle)
    latest_q = (
        select(Article)
        .filter(filters)
        .options(load_only(Article.alias, Article.title,
                           Article.image, Article.published_date))
        .order_by(Article.published_date.desc())
        .limit(5)
    )
    latest = (await db.execute(latest_q)).scalars().all()

    return {
        "article": article,
        "latest_articles": latest,
        "related_articles": related_articles,
        "authors": authors,
    }


# --------------------------------------------------------------------------- #
#  AMP-страница
#  (упрощённая логика, всегда работает с Article)
# --------------------------------------------------------------------------- #
async def article_amp(db: AsyncSession, slug: str, curr_redis):
    dt = datetime.now() + TZ_SHIFT
    filters = and_(Article.article_status == "P", Article.published_date <= dt)

    # ── 1. Пытаемся вытащить из Redis ─────────────────────────────────────────
    try:
        cached = await curr_redis.get(f"article_amp_{slug}")
        if cached:
            article: Article = loads(cached)
        else:
            raise KeyError
    except Exception:
        query = (
            select(Article)
            .filter(filters, Article.alias == slug)
            .options(selectinload(Article.categories), selectinload(Article.tags))
        )
        article = await get_object_or_404(query=query, session=db)
        try:
            await curr_redis.set(f"article_amp_{slug}", dumps(article))
        except RedisError as e:
            logging.error(f"Redis SET error: {e}")

    # ── 2. Преобразование контента в AMP ──────────────────────────────────────
    text = parse.unquote(article.content).replace("\n", "")
    amp_scripts = ""

    # Facebook
    facebook_reg = r"<iframe.*?src=.*?facebook.com.*?href=(.*?);.*?<\/iframe>"
    if re.search(facebook_reg, text):
        amp_scripts += '<script async custom-element="amp-facebook" src="https://cdn.ampproject.org/v0/amp-facebook-0.1.js"></script>\n'
    for x in re.finditer(facebook_reg, text):
        href = x.group(1)
        text = text.replace(
            x.group(),
            f'<amp-facebook width="1" height="1" layout="responsive" data-href="{href}"></amp-facebook>',
        )

    # Instagram
    insta_reg = r'<(blockquote|iframe) class="instagram-media.*?instagram.com\/.*?\/(.*?)\/.*?<\/(blockquote|iframe)>'
    if re.search(insta_reg, text):
        amp_scripts += '<script async custom-element="amp-instagram" src="https://cdn.ampproject.org/v0/amp-instagram-0.1.js"></script>\n'
    for x in re.finditer(insta_reg, text):
        post_id = x.group(2)
        text = text.replace(
            x.group(),
            f'<amp-instagram data-shortcode="{post_id}" width="1" height="1" layout="responsive"></amp-instagram>',
        )

    # TikTok
    tiktok_reg = r'<(blockquote|iframe)[^>]*class="tiktok-embed".*?data-video-id="(.*?)">.*?<\/(blockquote|iframe)>'
    if re.search(tiktok_reg, text):
        amp_scripts += '<script async custom-element="amp-tiktok" src="https://cdn.ampproject.org/v0/amp-tiktok-0.1.js"></script>\n'
    for x in re.finditer(tiktok_reg, text):
        post_id = x.group(2)
        text = text.replace(
            x.group(),
            f'<amp-tiktok width="325" height="575" data-src="{post_id}"></amp-tiktok>',
        )

    # <picture>
    picture_reg = r"<picture>.*?srcset=\"(.*?)\".*?<\/picture>"
    for x in re.finditer(picture_reg, text):
        src = x.group(1)
        text = text.replace(
            x.group(),
            f'<amp-img src="{src}" width="800" height="450" layout="responsive"></amp-img>' if src else "",
        )

    # <img>
    img_reg = r"<img.*?src=\"(.*?)\".*?>"
    for x in re.finditer(img_reg, text):
        src = x.group(1)
        text = text.replace(
            x.group(),
            f'<amp-img src="{src}" width="800" height="450" layout="responsive"></amp-img>' if src else "",
        )

    # Удаляем <script>
    text = re.sub(r"<script.*?</script>", "", text, flags=re.S)

    # Twitter
    twitter_reg = r'<blockquote.*?class="twitter-tweet.*?twitter.*?/(\d+).*?</blockquote>'
    if re.search(twitter_reg, text):
        amp_scripts += '<script async custom-element="amp-twitter" src="https://cdn.ampproject.org/v0/amp-twitter-0.1.js"></script>\n'
    for x in re.finditer(twitter_reg, text):
        tweet_id = x.group(1)
        text = text.replace(
            x.group(),
            f'<amp-twitter width="375" height="472" layout="responsive" data-tweetid="{tweet_id}"></amp-twitter>',
        )

    # YouTube
    youtube_reg = r"<iframe.*?youtube.com/embed/([a-zA-Z0-9_-]+).*?</iframe>"
    if re.search(youtube_reg, text):
        amp_scripts += '<script async custom-element="amp-youtube" src="https://cdn.ampproject.org/v0/amp-youtube-0.1.js"></script>\n'
    for x in re.finditer(youtube_reg, text):
        video_id = x.group(1)
        text = text.replace(
            x.group(),
            f'<amp-youtube data-videoid="{video_id}" layout="responsive" width="480" height="270"></amp-youtube>',
        )

    # Очистка мусора
    text = re.sub(
        r'(onclick=".*?"|onmouseover=".*?"|type=".*?"|<hr.*?>|<iframe.*?</iframe>|async="true"|clear=all|<object.*?</object>|style=".*?"|style=\'.*?\'|<style.*?</style>|<h1.*?</h1>|<meta.*?>|<title.*?</title>|<pucture.*?</picture>)',
        "",
        text,
        flags=re.S,
    )
    text = re.sub(r'\scontenteditable(="[^"]*"|=\'[^\']*\'|)', "", text)
    text = re.sub(r'\snowrap(="[^"]*"|=\'[^\']*\'|)', "", text)

    # ── 3. Авторы и похожие статьи ────────────────────────────────────────────
    authors = [await user_rpc.user_by_uid(uid) for uid in article.author_ids]
    authors = [a for a in authors if a]

    category_ids = [cat.id for cat in article.categories]
    related_query = (
        select(Article)
        .join(article_category)
        .join(Category)
        .filter(filters, Article.id != article.id, Category.id.in_(category_ids))
        .order_by(Article.published_date.desc())
        .limit(5)
    )
    related_articles = (await db.execute(related_query)).scalars().all()

    # ── 4. Итоговый контекст ─────────────────────────────────────────────────
    context = {
        "id": article.id,
        "title": article.title,
        "image": article.image,
        "content": text,
        "published_date": article.published_date,
        "datetime_updated": article.datetime_updated,
        "description": article.description,
        "tags": article.tags,
        "alias": article.alias,
        "authors": authors,
        "categories": article.categories,
        "article": article,
        "related_articles": related_articles,
        "content_type": "articles",
        "amp_scripts": amp_scripts,
    }

    return context

async def get_all_articles(db: AsyncSession, page: int):
    """
    Лента всех опубликованных материалов.
    """
    dt = datetime.now() + TZ_SHIFT
    filters = and_(
        Article.published_date <= dt,
        Article.article_status == "P"
    )

    query = (
        select(Article)
        .filter(filters)
        .options(selectinload(Article.categories))
        .order_by(Article.published_date.desc())
    )

    pagination = Pagination(page=page, per_page=10)
    page_obj = await paginate(db, pagination, query)

    return {"page": page_obj}

# --------------------------------------------------------------------------- #
#  Реклама
# --------------------------------------------------------------------------- #
# async def article_ads(db: AsyncSession, page: int = 1, status: str = "P"):
#     """
#     :param status: 'P' — опубликованные, 'D' — черновики-реклама
#     """
#     filters = and_(
#         Article.article_status == status,
#         Article.is_advertising.is_(True),
#     )
#
#     query = (
#         select(Article)
#         .filter(filters)
#         .options(load_only(Article.alias, Article.title,
#                            Article.image, Article.published_date))
#         .order_by(Article.published_date.desc())
#     )
#
#     pagination = Pagination(page=page, per_page=18)
#     page_obj = await paginate(db, pagination, query)
#
#     return {"page": page_obj, "status": status}
