import sqlalchemy as sa
from sqlalchemy import UniqueConstraint

from src.models.base import Base, UUIDMixin
from src.models.choices import ModuleTypeEnum
from sqlalchemy.dialects.postgresql import ARRAY, JSON


class PageStructureManager(UUIDMixin, Base):
    __tablename__ = "tbl_page_structure"

    name = sa.Column(sa.String(30), nullable=False)
    page_url = sa.Column(sa.String(255), nullable=False)
    order = sa.Column(sa.Integer, nullable=False)
    module_type = sa.Column(sa.Enum(ModuleTypeEnum), nullable=False)
    prefix = sa.Column(sa.String(255), nullable=True)
    suffix = sa.Column(sa.String(255), nullable=True)
    sub_modules = sa.Column(ARRAY(JSON), default=[], nullable=True)

    def __repr__(self):
        return f"{self.name}"
