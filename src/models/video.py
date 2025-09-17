import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import JSON

from src.models.base import Base, UUIDMixin, CreatedUpdatedMixin


class Video(UUIDMixin, Base, CreatedUpdatedMixin):
    __tablename__ = "tbl_video"
    video_url = sa.Column(sa.String(300))
    video_id = sa.Column(sa.String(300))
    # image = sa.Column(JSON, default=dict)
