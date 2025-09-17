# src/models/base.py

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class UUIDMixin:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True)


class CreatedUpdatedMixin:
    datetime_updated = Column(DateTime, onupdate=func.now())
    datetime_created = Column(DateTime, default=func.now())
