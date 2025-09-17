# src/models/draft_article.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.orm import relationship, backref

from src.models.base import Base, UUIDMixin
from src.models.category import Category
from src.models.tags import Tag

draft_tag = sa.Table(
    "news_draftarticle_tags",
    Base.metadata,
    sa.Column("draftarticle_id", UUID(as_uuid=True),
              sa.ForeignKey("news_draftarticle.id", ondelete="CASCADE")),
    sa.Column("tag_id", UUID(as_uuid=True),
              sa.ForeignKey("news_tag.id", ondelete="CASCADE")),
)

draft_category = sa.Table(
    "news_draftarticle_categories",
    Base.metadata,
    sa.Column("draftarticle_id", UUID(as_uuid=True),
              sa.ForeignKey("news_draftarticle.id", ondelete="CASCADE")),
    sa.Column("category_id", UUID(as_uuid=True),
              sa.ForeignKey("news_category.id", ondelete="CASCADE")),
)


class DraftArticle(UUIDMixin, Base):
    __tablename__ = "news_draftarticle"

    title = sa.Column(sa.String(1000))
    alias = sa.Column(sa.String(1000), unique=True, nullable=False)
    description = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    datetime_created = sa.Column(sa.DateTime, default=sa.func.now())
    author_id = sa.Column(UUID(as_uuid=True))
    image = sa.Column(JSON, default=dict)
    request_url = sa.Column(sa.String)

    categories = relationship(
        Category, secondary=draft_category,
        backref=backref("draftarticles", lazy=True),
    )
    tags = relationship(
        Tag, secondary=draft_tag,
        backref=backref("draftarticles", lazy=True),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DraftArticle {self.title!r}>"
