"""
SQLAlchemy ORM model for application users.

Roles
-----
  Admin       – Full access to every endpoint.
  SOCAnalyst  – Manage incidents, run playbooks, generate reports.
  Viewer      – Read-only access (GET endpoints only).
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String

from app.database.db import Base


class UserRole(str, enum.Enum):
    Admin      = "Admin"
    SOCAnalyst = "SOCAnalyst"
    Viewer     = "Viewer"


class User(Base):
    """Application user with role-based access control."""

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True, autoincrement=True)

    username: str = Column(String(80), unique=True, nullable=False, index=True)
    email: str    = Column(String(255), unique=True, nullable=False, index=True)
    full_name: str = Column(String(150), nullable=True)

    hashed_password: str = Column(String(255), nullable=False)

    role: str = Column(
        SAEnum(UserRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=UserRole.Viewer,
    )

    is_active: bool = Column(Boolean, default=True, nullable=False)

    created_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: datetime = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User username={self.username!r} role={self.role} active={self.is_active}>"
