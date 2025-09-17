# src/models/tag.py
import sqlalchemy as sa
from src.models.base import Base, UUIDMixin


class Tag(UUIDMixin, Base):
    __tablename__ = "news_tag"

    title = sa.Column(sa.String(250), nullable=False, index=True)
    seo_title = sa.Column(sa.String(250))
    tag_name = sa.Column(sa.String(250))
    slug = sa.Column(sa.String(250), unique=True, nullable=False, index=True)
    description = sa.Column(sa.Text, default="", nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tag {self.title!r}>"
