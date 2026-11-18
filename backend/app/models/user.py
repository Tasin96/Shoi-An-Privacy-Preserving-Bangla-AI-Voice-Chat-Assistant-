import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.db.session import Base

class User(Base):
    """
    Pseudonymous user model.
    NO PII: No name, phone number, email or physical address.
    Only a random client-generated or server-generated UUID.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    pin_hash = Column(String(128), nullable=True)
    age_group = Column(String(20), nullable=True)
    language = Column(String(10), default="bn")

    # Cascading relationships so "Delete all my data" completely wipes everything
    period_logs = relationship("PeriodLog", back_populates="user", cascade="all, delete-orphan")
    mood_logs = relationship("MoodLog", back_populates="user", cascade="all, delete-orphan")
    habit_logs = relationship("HabitLog", back_populates="user", cascade="all, delete-orphan")
    pcos_checks = relationship("PCOSCheck", back_populates="user", cascade="all, delete-orphan")
    pregnancy_logs = relationship("PregnancyLog", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
