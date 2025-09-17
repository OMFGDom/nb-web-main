# src/models/category.py
import sqlalchemy as sa
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import UUID

from src.models.base import Base, UUIDMixin


class Category(UUIDMixin, Base):
    __tablename__ = "news_category"

    slug = sa.Column(sa.String(250), nullable=False, unique=True, index=True)
    title = sa.Column(sa.String(250), nullable=False, index=True)
    seo_title = sa.Column(sa.String(250))
    description = sa.Column(sa.Text, default="", nullable=True)
    level = sa.Column(sa.Integer, default=1)
    is_active = sa.Column(sa.Boolean, default=True)

    parent_category_id = sa.Column(
        UUID(as_uuid=True), sa.ForeignKey("news_category.id"), nullable=True
    )
    children = relationship(
        "Category",
        backref=backref("parent", remote_side="Category.id"),
        lazy="selectin",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Category {self.title!r}>"
