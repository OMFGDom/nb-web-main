from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from src.models.page_structure import PageStructureManager


async def page_structure(db: AsyncSession):
    header_result = await db.execute(
        select(PageStructureManager)
        .filter(PageStructureManager.module_type=='header')
        .order_by(PageStructureManager.order)
    )
    header = header_result.scalars().all()
    print("works, works!!")
    footer_result = await db.execute(
        select(PageStructureManager)
        .filter(PageStructureManager.module_type=='footer')
        .order_by(PageStructureManager.order)
    )
    footer = footer_result.scalars().all()
    menu_result = await db.execute(
        select(PageStructureManager)
        .filter(PageStructureManager.module_type == 'menu')
        .order_by(PageStructureManager.order)
    )
    menu = menu_result.scalars().all()


    context = {'header': header, 'footer': footer, "menu": menu}
    return context


