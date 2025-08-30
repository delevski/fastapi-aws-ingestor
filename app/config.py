import os
from dataclasses import dataclass
from typing import Literal


@dataclass
class Settings:
    """Application settings loaded from environment variables."""
    
    storage_backend: Literal["s3", "dynamodb"] = "s3"
    aws_region: str = "us-east-1"
    s3_bucket: str | None = None
    ddb_table: str | None = None
    log_level: str = "INFO"
    service_name: str = "fastapi-aws-ingestor"
    
    def __post_init__(self) -> None:
        """Load settings from environment variables."""
        self.storage_backend = os.getenv("STORAGE_BACKEND", self.storage_backend)
        self.aws_region = os.getenv("AWS_REGION", self.aws_region)
        self.s3_bucket = os.getenv("S3_BUCKET", self.s3_bucket)
        self.ddb_table = os.getenv("DDB_TABLE", self.ddb_table)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        self.service_name = os.getenv("SERVICE_NAME", self.service_name)


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
