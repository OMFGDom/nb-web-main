# src/models/podcast.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON, ARRAY

from src.models.base import Base, UUIDMixin, CreatedUpdatedMixin


class Podcast(UUIDMixin, CreatedUpdatedMixin, Base):
    __tablename__ = "news_podcast"

    # базовые поля
    title = sa.Column(sa.String, nullable=False, index=True)
    category_title = sa.Column(sa.String, nullable=False, index=True)

    alias = sa.Column(sa.String, nullable=False, unique=True, index=True)
    description = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    published_date = sa.Column(sa.DateTime, index=True)

    # медиа/данные
    image = sa.Column(JSON, default=dict)
    podcast = sa.Column(JSON, default=dict)

    # авторство
    author_ids = sa.Column(ARRAY(sa.String(36)))

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Podcast {self.title!r}>"
