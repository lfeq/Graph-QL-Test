import uuid
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLAlchemyEnum, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.schema import UniqueConstraint
from enum import Enum
from .db import Base

class ProcessingStatus(Enum):
    """
    Represents the status of a background processing task, typically for image generation.
    """
    PENDING = "PENDING"  # Task is awaiting processing.
    COMPLETED = "COMPLETED"  # Task has finished successfully.
    FAILED = "FAILED"  # Task encountered an error and did not complete.

class FutureViewing(Base):
    """
    Represents a 'future viewing' concept, storing user-provided data
    and an associated generated image URL and processing status.

    Attributes:
        id (uuid.UUID): Primary key, unique identifier for the future viewing.
        name (str): Name associated with the viewing.
        age (int): Age associated with the viewing.
        content (str): Content or prompt for the viewing.
        created_at (datetime): Timestamp of when the record was created.
        image_url (str, optional): URL of the generated image, if available.
        status (ProcessingStatus): Current processing status of the image generation.
    """
    __tablename__ = "future_viewings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    age = Column(Integer, nullable=False)
    content = Column(String(4000), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    image_url = Column(String, nullable=True)
    status = Column(SQLAlchemyEnum(ProcessingStatus), default=ProcessingStatus.PENDING, nullable=False)

    def to_dict(self):
        """
        Returns a dictionary representation of the FutureViewing instance,
        suitable for serialization (e.g., in API responses).

        Returns:
            dict: A dictionary containing key-value pairs for the model's attributes.
                  The 'id' is converted to a string, and 'createdAt' is ISO formatted.
        """
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
    """
    Represents a display screen that can show FutureViewings.

    Attributes:
        id (uuid.UUID): Primary key, unique identifier for the screen.
        name (str, optional): An optional friendly name for the screen (e.g., "Lobby Screen").
        created_at (datetime): Timestamp of when the screen record was created.
    """
    __tablename__ = "screens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=True) # Optional friendly name
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def to_dict(self):
        """
        Returns a dictionary representation of the Screens instance,
        suitable for serialization.

        Returns:
            dict: A dictionary containing key-value pairs for the model's attributes.
                  The 'id' is converted to a string, and 'createdAt' is ISO formatted.
        """
        return {
            "id": str(self.id),
            "name": self.name,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

class ScreenViewings(Base):
    """
    Represents the event of a specific FutureViewing being shown on a specific Screen.
    This acts as a join table to track which future viewings have been displayed on which screens.

    Attributes:
        id (uuid.UUID): Primary key, unique identifier for this viewing event.
        future_viewing_id (uuid.UUID): Foreign key linking to the FutureViewing record.
        screen_id (uuid.UUID): Foreign key linking to the Screens record.
        viewed_at (datetime): Timestamp of when the FutureViewing was displayed on the screen.
    """
    __tablename__ = "screen_viewings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    future_viewing_id = Column(UUID(as_uuid=True), ForeignKey("future_viewings.id"), nullable=False)
    screen_id = Column(UUID(as_uuid=True), ForeignKey("screens.id"), nullable=False)
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (UniqueConstraint('future_viewing_id', 'screen_id', name='_future_viewing_screen_uc'),)
