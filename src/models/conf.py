import sqlalchemy as sa

from src.models.base import Base, UUIDMixin


class DynamicConf(UUIDMixin, Base):
    __tablename__ = "tbl_dynamic_conf"

    attr_key = sa.Column(sa.String(10))
    attr_val = sa.Column(sa.String(20))

