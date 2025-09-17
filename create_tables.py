from sqlalchemy import create_engine
from src.models.base import Base

import os
from logging import config as logging_config
import sqlalchemy as sa
from sqlalchemy import ForeignKey, func
from sqlalchemy.dialects.postgresql import JSON, ARRAY

from src.models.base import Base, UUIDMixin


class ErrorReport(UUIDMixin, Base):
    __tablename__ = "tbl_error_reports"

    datetime_created = sa.Column(sa.DateTime, default=func.now())
    text = sa.Column(sa.String(300))
    error_description = sa.Column(sa.String(500))
    page_url = sa.Column(sa.String)
from src.core.logger import LOGGING

logging_config.dictConfig(LOGGING)

C_DATABASE_URL = os.getenv('DATABASE_URL', os.getenv('SYNC_DATABASE_URL', 'postgresql://postgres:bkm@localhost:5432/forbes_test'))

db_engine = create_engine(C_DATABASE_URL, echo=True, pool_pre_ping=True)
Base.metadata.create_all(bind=db_engine)


