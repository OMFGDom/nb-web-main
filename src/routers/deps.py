from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from src.db.database import get_db
from typing import Annotated

DBSessionDep = Annotated[AsyncSession, Depends(get_db)]
