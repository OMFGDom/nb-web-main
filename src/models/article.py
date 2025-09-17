# src/models/article.py
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, ARRAY
from sqlalchemy.orm import relationship, backref

from src.models.base import Base, UUIDMixin, CreatedUpdatedMixin
from src.models.category import Category
from src.models.tags import Tag
from src.models.sitemap_config import SiteMapConfig

# ─── M2M таблицы ───────────────────────────────────────────────────────────────
article_tag = sa.Table(
    "news_article_tags",
    Base.metadata,
    sa.Column("article_id", UUID(as_uuid=True),
              sa.ForeignKey("news_article.id", ondelete="CASCADE")),
    sa.Column("tag_id", UUID(as_uuid=True),
              sa.ForeignKey("news_tag.id", ondelete="CASCADE")),
    sa.Column("position", sa.Integer, nullable=True),
)

article_category = sa.Table(
    "news_article_categories",
    Base.metadata,
    sa.Column("article_id", UUID(as_uuid=True),
              sa.ForeignKey("news_article.id", ondelete="CASCADE")),
    sa.Column("category_id", UUID(as_uuid=True),
              sa.ForeignKey("news_category.id", ondelete="CASCADE")),
)

article_sitemap = sa.Table(
    "news_article_site_map_conf",
    Base.metadata,
    sa.Column("article_id", UUID(as_uuid=True),
              sa.ForeignKey("news_article.id", ondelete="CASCADE")),
    sa.Column("sitemapconfig_id", UUID(as_uuid=True),
              sa.ForeignKey("news_sitemapconfig.id", ondelete="CASCADE")),
)
# ───────────────────────────────────────────────────────────────────────────────


class Article(UUIDMixin, CreatedUpdatedMixin, Base):
    __tablename__ = "news_article"

    # контент
    title = sa.Column(sa.String, nullable=False, index=True)
    alias = sa.Column(sa.String, nullable=False, unique=True, index=True)
    description = sa.Column(sa.Text)
    content = sa.Column(sa.Text)
    published_date = sa.Column(sa.DateTime, index=True)

    # медиа
    image = sa.Column(JSON, default=dict)

    # авторство / аудит
    changed_user = sa.Column(JSON, default=dict)
    author_ids = sa.Column(ARRAY(sa.String(36)))
    pseudonym = sa.Column(sa.String(50))
    editor = sa.Column(sa.String(36))
    # editor_id = sa.Column(UUID(as_uuid=True))

    # метрики / статусы
    view_count = sa.Column(sa.Integer, default=0)
    locked = sa.Column(sa.Boolean, default=False)
    lock_time = sa.Column(sa.DateTime)
    article_status = sa.Column(sa.String(3), default="D", index=True)

    # публикация
    public_params = sa.Column(sa.Integer, default=0)
    public_types = sa.Column(ARRAY(sa.String), default=[])
    news_source = sa.Column(sa.JSON, nullable=True, default=None)
    # is_advertising = sa.Column(sa.Boolean, default=False)

    # связи
    categories = relationship(
        Category,
        secondary=article_category,
        backref=backref("articles", lazy=True),
    )
    tags = relationship(
        Tag,
        secondary=article_tag,
        backref=backref("articles", lazy=True),
        order_by=article_tag.c.position,
    )
    site_map_conf = relationship(
        SiteMapConfig,
        secondary=article_sitemap,
        backref=backref("articles", lazy=True),
    )
    fixed_article = relationship("FixedArticle", back_populates="article",
                                 uselist=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Article {self.title!r}>"
