# src/models/fixed_article.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.models.base import Base, UUIDMixin


class FixedArticle(UUIDMixin, Base):
    __tablename__ = "news_fixedarticle"

    article_id = sa.Column(UUID(as_uuid=True),
                           sa.ForeignKey("news_article.id"))
    order = sa.Column(sa.Integer, unique=True)

    article = relationship("Article", back_populates="fixed_article",
                           uselist=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<FixedArticle order={self.order}>"
