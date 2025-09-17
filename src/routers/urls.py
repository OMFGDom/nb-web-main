from datetime import datetime

from fastapi import APIRouter, Request, Depends, Query, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, desc, and_
from sqlalchemy.orm import selectinload
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.models.article import Article
from src.services.article import TZ_SHIFT
from src.services.error import get_articles_404
from src.services.index import get_index, load_more
from src.services.category import get_category
from src.services.tag import get_tag
from src.services import article as article_service
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
templates.env.filters['pretty_date'] = pretty_date.pretty_date
templates.env.filters['announce_date'] = pretty_date.announce_date
templates.env.filters['article_pretty_date'] = pretty_date.article_pretty_date
templates.env.filters['format_number'] = format_number.format_number


# @router.get('/search')
# async def search(
#     request: Request,
#     db: DBSessionDep,
#     q: str = "",
#     page: int = Query(default=1, ge=1),
#     s: str = None,
#     es: AsyncElasticsearch = Depends(get_elastic),
#     author: str = None,
# ):
#     # sort_by = 'published_date:desc' if s == 'data' else None
#     # articles_search = ArticlesImprovedSearch(index="articles", sort_param=sort_by)
#     # total = 0
#     # result = []
#     # per_page = 6
#     #
#     # if q or author:
#     #     await articles_search.search(search_val=q)
#     #     elastic_result = await articles_search.get(
#     #         elastic_session=es,
#     #         from_=page,
#     #         per_page=per_page,
#     #         author=author
#     #     )
#     #     total = elastic_result['hits']['total']['value']
#     #     result = [item['_source'] for item in elastic_result['hits']['hits']]
#     dt = datetime.now() + TZ_SHIFT
#     filters = and_(
#         Article.published_date <= dt,
#         Article.article_status == "P"
#     )
#     query = select(Article).options(selectinload(Article.categories)).filter(filters)
#     if s == 'data':
#         query = query.order_by(Article.published_date.desc())
#
#     if q:
#         query = query.filter(Article.title.ilike(f'%{q}%'))
#
#     # if author:
#     #     query = query.filter(Article.author_ids.in_([author]))
#
#
#     # total_pages = (total + per_page - 1) // per_page
#     pagination = Pagination(page=page, per_page=10)
#     page_obj = await paginate(db, pagination, query)
#     # data = PaginationResponse(
#     #     page=page,
#     #     per_page=per_page,
#     #     pages=total_pages,
#     #     total=total,
#     #     items=query,
#     #     has_previous=page > 1,
#     #     has_next=page < total_pages,
#     # )
#     context = {
#         "total": page_obj.total,
#         "q": q,
#         "page": page_obj,
#         "page_number": page,
#         "s": s,
#         # "author": author
#     }
#     return templates.TemplateResponse(request=request, name="pages/search-test.html", context=context)

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


# @router.get('/api/authors')
# async def api_authors():
#     return await api_author()


@router.get('/')
@cache_response(redis_key_prefix="index_page", expiration=60)
async def index(request: Request, db: DBSessionDep):
    context = await get_index(db=db)
    return templates.TemplateResponse(request=request, name="pages/index.html", context=context)


# @router.get('/api/load-more')
# async def loadmore(db: DBSessionDep, page: int = 1):
#     return await load_more(db=db, page=page)


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

@router.get('/amp/{slug}/')
async def amp_article(
    request: Request,
    db: DBSessionDep,
    slug: str,
    curr_redis = Depends(get_redis),   # ← добавили
):
    context = await article_service.article_amp(
        db=db,
        slug=slug,
        curr_redis=curr_redis,         # ← передаём
    )
    return templates.TemplateResponse(
        request=request,
        name="pages/amp_article.html",
        context=context
    )


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

@router.get('/data/')
async def data(request: Request):
    return templates.TemplateResponse(request=request, name="pages/data.html", context={})

@router.get('/advertising/')
async def advertising(request: Request):
    return templates.TemplateResponse(request=request, name="pages/advertising.html", context={})

@router.get('/material-use-policy/')
async def material_use_policy(request: Request):
    return templates.TemplateResponse(request=request, name="pages/material-use-policy.html", context={})

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
