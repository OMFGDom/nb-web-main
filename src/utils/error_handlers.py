from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException as StarletteHTTPException

async def get_object_or_404(query, session: AsyncSession):
    instance = await session.execute(query)
    result = instance.scalar()
    if result is None:
        raise HTTPException(status_code=404, detail=f"Not found")
    return result
