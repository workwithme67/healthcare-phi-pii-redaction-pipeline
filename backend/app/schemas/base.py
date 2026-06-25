"""
HealthTech PHI/PII Redaction Pipeline
Pydantic Schemas — Base

Shared configuration and base class for all response/request schemas.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """
    Base Pydantic model with shared configuration.

    - `from_attributes=True`  → enables ORM mode (SQLAlchemy → Pydantic)
    - `populate_by_name=True` → allows both alias and field name
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
    )


class TimestampMixin(AppBaseModel):
    """Mixin that adds standard timestamp fields."""
    created_at: datetime
    updated_at: datetime | None = None
