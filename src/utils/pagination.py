from typing import List, Annotated
from sqlalchemy import func, select
from fastapi import Query
from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: Annotated[int, Field(1, ge=1)]
    per_page: Annotated[int, Field(20, gt=0, le=100)]


class PaginationResponse(BaseModel):
    page: Annotated[int, Field(1, gt=0)]
    per_page: Annotated[int, Field(20, gt=0, le=100)]
    pages: int = Query(gte=0)
    total: int = Query(gte=0)
    items: List = []
    has_previous: bool = False
    has_next: bool = False


async def paginate(session, pagination, query):
    count_query = select(func.count()).select_from(query)
    total = (await session.execute(count_query)).scalar()
    query = query.offset((pagination.page - 1) * pagination.per_page).limit(pagination.per_page)
    result = (await session.execute(query)).scalars()

    total_pages = (total + pagination.per_page - 1) // pagination.per_page
    has_previous = True if pagination.page > 1 else False
    has_next = True if pagination.page < total_pages else False
    return PaginationResponse(
        page=pagination.page,
        per_page=pagination.per_page,
        pages=total_pages,
        total=total,
        items=result,
        has_previous=has_previous,
        has_next=has_next,
    )
