from datetime import datetime
import os
from fastapi import APIRouter, Request, Depends, Query, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.models.article import Article
from src.services.article import TZ_SHIFT
from src.services.error import get_articles_404
from src.services.index import get_index
from src.services.category import get_category
from src.services.tag import get_tag
from src.services import article as article_service
from src.services import podcast as podcast_service
from src.services.base import get_base
from src.services.author import get_authors, author_detail, api_author
from src.services.search import search_results
from src.utils.decorators import cache_response
from src.template_tags import pretty_date, format_number
from src.db.redis import get_redis
from src.db.elastic import get_elastic
from src.routers.deps import DBSessionDep
from src.db.database import db_session_manager
from src.elastic.modules import ArticlesImprovedSearch
from src.elastic.schema import PaginationResponse
from elasticsearch import AsyncElasticsearch
from src.services.search import search_results
from src.utils.pagination import Pagination, paginate
from fastapi.responses import RedirectResponse

router = APIRouter(tags=["App"])

templates = Jinja2Templates(directory="templates")
SITE_URL = os.getenv("SITE_URL", "https://nationalbusiness.kz")
templates.env.globals['SITE_URL'] = SITE_URL
templates.env.filters['pretty_date'] = pretty_date.pretty_date
templates.env.filters['announce_date'] = pretty_date.announce_date
templates.env.filters['article_pretty_date'] = pretty_date.article_pretty_date
templates.env.filters['format_number'] = format_number.format_number
templates.env.filters['duration_mmss'] = pretty_date.duration_mmss
templates.env.filters['duration_hhmm'] = pretty_date.duration_hhmm
templates.env.filters['duration_minutes_only'] = pretty_date.duration_minutes_only

@router.get('/search')
async def search(
    request: Request,
    db: DBSessionDep,
    q: str = "",
    page: int = Query(default=1, ge=1),
    s: str = None,
):
    result = await search_results(db=db, page_number=page, q=q, sort=s)

    context = {
        "total": result["page"].total,
        "q": result["q"],
        "page": result["page"],
        "page_number": result["page_number"],
        "s": result["sort"],
    }
    return templates.TemplateResponse(request=request, name="pages/search-test.html", context=context)


@router.get('/')
@cache_response(redis_key_prefix="index_page", expiration=60)
async def index(request: Request, db: DBSessionDep):
    context = await get_index(db=db)
    return templates.TemplateResponse(request=request, name="pages/index.html", context=context)


@router.get('/news/{slug}/', name="article_detail")
async def articles(request: Request, db: DBSessionDep, slug: str, response: Response, curr_redis=Depends(get_redis)):
    context = await article_service.article_detail(db=db, slug=slug, curr_redis=curr_redis)
    return templates.TemplateResponse(request=request, name="pages/article.html", context=context)


@router.get('/preview/{uid}/')
async def articles_preview(request: Request, db: DBSessionDep, uid: str):
    context = await article_service.article_preview(db=db, uid=uid)
    return templates.TemplateResponse(request=request, name="pages/article-preview.html", context=context)


@router.get('/allnews/', name="allnews")
async def allnews(request: Request, db: DBSessionDep, page: int = 1):
    context = await article_service.get_all_articles(db=db, page=page)
    return templates.TemplateResponse(request=request,
                                      name="pages/allnews.html",
                                      context=context)


@router.get('/category/{slug}/')
@cache_response(redis_key_prefix="category_page", expiration=60)
async def category(request: Request, db: DBSessionDep, slug: str, page: int = Query(default=1, ge=1)):
    context = await get_category(db=db, slug=slug, page=page)
    return templates.TemplateResponse(request=request, name="pages/category.html", context=context)


@router.get('/tag/{slug}/')
@cache_response(redis_key_prefix="tag_page", expiration=60)
async def tag(request: Request, db: DBSessionDep, slug: str, page: int = Query(default=1, ge=1)):
    context = await get_tag(db=db, slug=slug, page=page)
    return templates.TemplateResponse(request=request, name="pages/tag.html", context=context)


@router.get('/authors/')
@cache_response(redis_key_prefix="authors_page", expiration=60)
async def authors(request: Request, db: DBSessionDep, page: int = Query(default=1, ge=1), q: str = ''):
    context = await get_authors(db=db, page=page, q=q)
    return templates.TemplateResponse(request=request, name="pages/authors.html", context=context)

@router.get('/author/{slug}/', include_in_schema=False)
async def redirect_author(slug: str, page: int = Query(default=1, ge=1)):
    return RedirectResponse(url=f"/authors/{slug}/?page={page}", status_code=307)
@router.get('/authors/{slug}/')
@cache_response(redis_key_prefix="author_page", expiration=60)
async def author(request: Request, db: DBSessionDep, slug: str, page: int = Query(default=1, ge=1)):
    context = await author_detail(db=db, uid=slug, page=page)
    return templates.TemplateResponse(request=request, name="pages/author.html", context=context)


@router.get('/contacts/')
async def contacts(request: Request):
    return templates.TemplateResponse(request=request, name="pages/contacts.html", context={})

@router.get('/podcasts/{slug}/', name="podcast_detail")
async def podcast_page(request: Request, db: DBSessionDep, slug: str, curr_redis=Depends(get_redis)):
    context = await podcast_service.podcast_detail(db=db, slug=slug, curr_redis=curr_redis)
    return templates.TemplateResponse(request=request, name="pages/podcast.html", context=context)

@router.get('/about/')
async def about(request: Request):
    return templates.TemplateResponse(request=request, name="pages/about.html", context={})

@router.get('/privacy-policy/')
async def privacy_policy(request: Request):
    return templates.TemplateResponse(request=request, name="pages/privacy-policy.html", context={})

async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        async with db_session_manager.session() as db:
            context = await get_articles_404(db=db)
        return templates.TemplateResponse(request=request, name="pages/404.html", context=context, status_code=404)


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    async with db_session_manager.session() as db:
        context = await get_articles_404(db=db)
    return templates.TemplateResponse(
        request=request,
        name="pages/404.html",
        context=context,
        errors=exc.errors(),
        status_code=422,
    )


async def generic_exception_handler(request: Request, exc: StarletteHTTPException):
    async with db_session_manager.session() as db:
        context = await get_articles_404(db=db)
    return templates.TemplateResponse(request=request, name="pages/404.html", context=context, status_code=500)
