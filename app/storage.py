import json
import logging
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import get_settings
from app.schemas import DataItemOut

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Custom exception for storage operations."""
    pass


class Storage(ABC):
    """Abstract storage interface."""
    
    @abstractmethod
    def store_batch(self, items: list[DataItemOut]) -> list[str]:
        """Store a batch of items and return storage keys."""
        pass


class S3Storage(Storage):
    """S3 storage implementation."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)
    
    def store_batch(self, items: list[DataItemOut]) -> list[str]:
        """Store items to S3 and return S3 keys."""
        keys = []
        
        for item in items:
            # Create S3 key: items/{id}-{received_at}.json
            key = f"items/{item.id}-{item.received_at.isoformat()}.json"
            
            try:
                # Convert item to JSON with datetime serialization
                item_data = item.model_dump(mode="json")
                
                # Upload to S3
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json.dumps(item_data, default=str),
                    ContentType="application/json"
                )
                
                keys.append(key)
                logger.info(f"Stored item {item.id} to S3: {key}")
                
            except (BotoCoreError, ClientError) as e:
                logger.exception(f"Failed to store item {item.id} to S3: {e}")
                raise StorageError(f"S3 storage error: {e}")
        
        return keys


class DynamoDBStorage(Storage):
    """DynamoDB storage implementation."""
    
    def __init__(self, table_name: str, region: str = "us-east-1"):
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
    
    def store_batch(self, items: list[DataItemOut]) -> list[str]:
        """Store items to DynamoDB and return storage keys."""
        keys = []
        
        for item in items:
            try:
                # Prepare item data with PK/SK pattern
                item_data = item.model_dump(mode="json")
                item_data["PK"] = item.id
                item_data["SK"] = item.sk
                
                # Convert float values to Decimal for DynamoDB compatibility
                def convert_floats_to_decimals(obj):
                    if isinstance(obj, dict):
                        return {k: convert_floats_to_decimals(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [convert_floats_to_decimals(v) for v in obj]
                    elif isinstance(obj, float):
                        return Decimal(str(obj))
                    else:
                        return obj
                
                item_data = convert_floats_to_decimals(item_data)
                
                # Put item to DynamoDB
                self.table.put_item(Item=item_data)
                
                # Create storage key: PK#{id}#SK#{sk}
                key = f"PK#{item.id}#SK#{item.sk}"
                keys.append(key)
                
                logger.info(f"Stored item {item.id} to DynamoDB: {key}")
                
            except (BotoCoreError, ClientError) as e:
                logger.exception(f"Failed to store item {item.id} to DynamoDB: {e}")
                raise StorageError(f"DynamoDB storage error: {e}")
        
        return keys


def get_storage_from_env() -> Storage:
    """Get storage backend based on environment configuration."""
    settings = get_settings()
    
    if settings.storage_backend == "s3":
        if not settings.s3_bucket:
            raise StorageError("S3_BUCKET environment variable is required for S3 storage")
        return S3Storage(settings.s3_bucket, settings.aws_region)
    
    elif settings.storage_backend == "dynamodb":
        if not settings.ddb_table:
            raise StorageError("DDB_TABLE environment variable is required for DynamoDB storage")
        return DynamoDBStorage(settings.ddb_table, settings.aws_region)
    
    else:
        raise StorageError(f"Unsupported storage backend: {settings.storage_backend}")
