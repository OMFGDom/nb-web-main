from typing import List, Annotated
from sqlalchemy import func, select
from fastapi import Query
from pydantic import BaseModel, Field
class PaginationResponse(BaseModel):
    page: Annotated[int, Field(1, gt=0)]
    per_page: Annotated[int, Field(20, gt=0, le=100)]
    pages: int = Query(gte=0)
    total: int = Query(gte=0)
    items: List = []
    has_previous: bool = False
    has_next: bool = False