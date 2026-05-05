"""
Database configuration using SQLAlchemy with SQLite.
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crm_hcp.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Interaction(Base):
    __tablename__ = "interactions"

    id               = Column(Integer, primary_key=True, index=True)
    hcp_name         = Column(String(255), nullable=True)
    interaction_type = Column(String(100), nullable=True)
    date             = Column(String(50),  nullable=True)
    time             = Column(String(20),  nullable=True)
    attendees        = Column(Text,        nullable=True)
    discussion_topic = Column(Text,        nullable=True)
    sentiment        = Column(String(50),  nullable=True)
    materials_shared = Column(Text,        nullable=True)
    brochure_shared  = Column(Boolean, default=False, nullable=True)
    follow_up_suggestion = Column(Text,   nullable=True)
    summary          = Column(Text,        nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)
    updated_at       = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id         = Column(Integer, primary_key=True, index=True)
    role       = Column(String(20), nullable=False)
    content    = Column(Text,       nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
