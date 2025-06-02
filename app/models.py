import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLAlchemyEnum, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint
from enum import Enum
from .db import Base

class ProcessingStatus(Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class FutureViewing(Base):
    __tablename__ = "future_viewings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    content = Column(String(4000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    image_url = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "age": self.age,
            "content": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "imageUrl": self.image_url,
            "status": self.status,
        }

class Screens(Base):
    __tablename__ = "screens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=True) # Optional friendly name
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

class ScreenViewings(Base):
    __tablename__ = "screen_viewings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    future_viewing_id = Column(UUID(as_uuid=True), ForeignKey("future_viewings.id"), nullable=False)
    screen_id = Column(UUID(as_uuid=True), ForeignKey("screens.id"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint('future_viewing_id', 'screen_id', name='_future_viewing_screen_uc'),)
