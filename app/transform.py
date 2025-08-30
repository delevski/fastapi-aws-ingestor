import re
from datetime import datetime, timezone

from app.schemas import DataItemIn, DataItemOut


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    # Convert to lowercase and replace non-alphanumeric chars with hyphens
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', text.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def transform_item(item: DataItemIn) -> DataItemOut:
    """Transform input data item to output format with computed fields."""
    
    # Use provided timestamp or default to now (UTC)
    timestamp = item.timestamp or datetime.now(timezone.utc)
    
    # Set received_at to now (UTC)
    received_at = datetime.now(timezone.utc)
    
    # Transform fields
    name_upper = item.name.upper()
    value_times_two = item.value * 2
    slug = slugify(item.name)
    sk = received_at.isoformat()
    
    return DataItemOut(
        id=item.id,
        name=item.name,
        value=item.value,
        timestamp=timestamp,
        metadata=item.metadata,
        slug=slug,
        name_upper=name_upper,
        value_times_two=value_times_two,
        received_at=received_at,
        sk=sk
    )
