
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    history = relationship("PredictionHistory", back_populates="owner")

class PredictionHistory(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Input Snapshot
    project_description = Column(Text)
    project_type = Column(String)
    complexity_score = Column(Integer)
    
    # Output Snapshot
    predicted_delay = Column(Float)
    cost_overrun = Column(Float)
    primary_suggestion = Column(String)
    
    timestamp = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="history")
