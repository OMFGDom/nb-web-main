# src/models/sitemap_config.py
import sqlalchemy as sa
from src.models.base import Base, UUIDMixin


class SiteMapConfig(UUIDMixin, Base):
    __tablename__ = "news_sitemapconfig"

    name = sa.Column(sa.String(255), nullable=False)
    key = sa.Column(sa.String(100), unique=True)
    is_active = sa.Column(sa.Boolean, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SiteMapConfig {self.name!r}>"
