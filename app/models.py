import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLAlchemyEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
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
    has_been_viewed = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "age": self.age,
            "content": self.content,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "imageUrl": self.image_url,
            "status": self.status,
            "hasBeenViewed": self.has_been_viewed,
        }