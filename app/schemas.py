from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DataItemIn(BaseModel):
    """Input data item schema."""
    
    id: str
    name: str
    value: float
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataBatch(BaseModel):
    """Batch of input data items."""
    
    items: list[DataItemIn] = Field(..., min_length=1)


class DataItemOut(BaseModel):
    """Output data item schema with transformed fields."""
    
    id: str
    name: str
    value: float
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    
    # Transformed fields
    slug: str
    name_upper: str
    value_times_two: float
    received_at: datetime
    sk: str
