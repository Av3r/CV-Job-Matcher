"""
src/database.py
===============
Persistence layer for SkillAlign AI — stores and retrieves match analysis history
using SQLAlchemy 2.x and a local SQLite database.
"""

from __future__ import annotations

import datetime
from typing import List

from sqlalchemy import (
    create_engine, String, Integer, DateTime, Text
)
from sqlalchemy.orm import (
    declarative_base, sessionmaker, Session
)
from sqlalchemy.orm import Mapped, mapped_column

# --- SQLAlchemy setup ---

DATABASE_URL = "sqlite:///data/history.db"
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)
Base = declarative_base()

# --- Model ---

class MatchHistoryRecord(Base):
    __tablename__ = "match_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    job_url: Mapped[str] = mapped_column(String(512), nullable=False)
    match_score: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    job_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    report_json: Mapped[str] = mapped_column(Text, nullable=False)

# --- Helpers ---

def init_db() -> None:
    """Create all tables in the database (if not exist)."""
    Base.metadata.create_all(engine)


def save_match_record(
    job_url: str,
    match_score: int,
    candidate_json: str,
    job_json: str,
    report_json: str,
) -> None:
    """Save a new match analysis record to the database."""
    record = MatchHistoryRecord(
        job_url=job_url,
        match_score=match_score,
        candidate_data_json=candidate_json,
        job_data_json=job_json,
        report_json=report_json,
    )
    with SessionLocal() as session:
        session.add(record)
        session.commit()


def get_all_records() -> List[MatchHistoryRecord]:
    """Return all match records, newest first."""
    with SessionLocal() as session:
        return (
            session.query(MatchHistoryRecord)
            .order_by(MatchHistoryRecord.created_at.desc())
            .all()
        )
