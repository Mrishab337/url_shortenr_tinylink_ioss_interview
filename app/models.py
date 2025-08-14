from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Boolean, Text
from datetime import datetime, timedelta
from .database import Base
from typing import Optional

class URLMap(Base):
    __tablename__ = "url_map"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_accessed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def is_expired(self) -> bool:
        return bool(self.expires_at and datetime.utcnow() > self.expires_at)
