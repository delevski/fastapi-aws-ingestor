import os
from datetime import datetime, timezone

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.main import app
from app.schemas import DataItemIn
from app.transform import transform_item

# Test client
client = TestClient(app)

# Helper payload with two items
test_payload = {
    "items": [
        {
            "id": "test-1",
            "name": "Test Item 1",
            "value": 10.5,
            "metadata": {"category": "test"}
        },
        {
            "id": "test-2", 
            "name": "Another Test Item!",
            "value": 25.0,
            "timestamp": "2024-01-01T12:00:00Z",
            "metadata": {"priority": "high"}
        }
    ]
}


class TestTransform:
    """Test data transformation functionality."""
    
    def test_transform_item_slug_upper_value_times_two(self):
        """Test that transform correctly computes slug, name_upper, and value_times_two."""
        item = DataItemIn(
            id="test-1",
            name="Test Item Name!",
            value=15.5
        )
        
        result = transform_item(item)
        
        assert result.slug == "test-item-name"
        assert result.name_upper == "TEST ITEM NAME!"
        assert result.value_times_two == 31.0
        assert result.received_at is not None
        assert result.sk == result.received_at.isoformat()
    
    def test_transform_item_with_timestamp(self):
        """Test transform with provided timestamp."""
        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        item = DataItemIn(
            id="test-1",
            name="Test",
            value=10.0,
            timestamp=timestamp
        )
        
        result = transform_item(item)
        
        assert result.timestamp == timestamp
        assert result.received_at is not None
        assert result.received_at != timestamp  # received_at should be now


class TestValidation:
    """Test input validation."""
    
    def test_validation_missing_required_field(self):
        """Test that missing required field triggers 422."""
        invalid_payload = {
            "items": [
                {
                    "id": "test-1",
                    # Missing 'name' field
                    "value": 10.0
                }
            ]
        }
        
        response = client.post("/ingest", json=invalid_payload)
        assert response.status_code == 422
    
    def test_validation_empty_items_list(self):
        """Test that empty items list triggers 422."""
        invalid_payload = {"items": []}
        
        response = client.post("/ingest", json=invalid_payload)
        assert response.status_code == 422


class TestS3Storage:
    """Test S3 storage functionality."""
    
    @mock_aws
    def test_s3_success(self):
        """Test successful S3 storage with moto."""
        # Set environment for S3 backend
        os.environ["STORAGE_BACKEND"] = "s3"
        os.environ["S3_BUCKET"] = "test-bucket"
        os.environ["AWS_REGION"] = "us-east-1"
        
        # Create mock S3 bucket
        s3_client = boto3.client("s3", region_name="us-east-1")
        s3_client.create_bucket(Bucket="test-bucket")
        
        # Make request
        response = client.post("/ingest", json=test_payload)
        
        assert response.status_code == 201
        result = response.json()
        assert result["stored"] == 2
        assert len(result["keys"]) == 2
        
        # Verify objects exist in S3
        for key in result["keys"]:
            head_response = s3_client.head_object(Bucket="test-bucket", Key=key)
            assert head_response["ResponseMetadata"]["HTTPStatusCode"] == 200
    
    @mock_aws
    def test_s3_failure_path(self):
        """Test S3 failure with nonexistent bucket."""
        # Set environment for S3 backend with nonexistent bucket
        os.environ["STORAGE_BACKEND"] = "s3"
        os.environ["S3_BUCKET"] = "nonexistent-bucket"
        os.environ["AWS_REGION"] = "us-east-1"
        
        # Make request
        response = client.post("/ingest", json=test_payload)
        
        assert response.status_code == 500
        result = response.json()
        assert "Storage error" in result["detail"]


class TestDynamoDBStorage:
    """Test DynamoDB storage functionality."""
    
    @mock_aws
    def test_dynamodb_success(self):
        """Test successful DynamoDB storage with moto."""
        # Set environment for DynamoDB backend
        os.environ["STORAGE_BACKEND"] = "dynamodb"
        os.environ["DDB_TABLE"] = "test-table"
        os.environ["AWS_REGION"] = "us-east-1"
        
        # Create mock DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName="test-table",
            KeySchema=[
                {"AttributeName": "PK", "KeyType": "HASH"},
                {"AttributeName": "SK", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "PK", "AttributeType": "S"},
                {"AttributeName": "SK", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        table.wait_until_exists()
        
        # Make request
        response = client.post("/ingest", json=test_payload)
        
        assert response.status_code == 201
        result = response.json()
        assert result["stored"] == 2
        assert len(result["keys"]) == 2
        
        # Verify items exist in DynamoDB
        scan_response = table.scan()
        assert scan_response["Count"] == 2


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_check(self):
        """Test health endpoint returns correct information."""
        # Set environment variables
        os.environ["STORAGE_BACKEND"] = "s3"
        os.environ["AWS_REGION"] = "us-west-2"
        
        response = client.get("/health")
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "ok"
        assert result["storage_backend"] == "s3"
        assert result["region"] == "us-west-2"


class TestRequestIDMiddleware:
    """Test request ID middleware."""
    
    def test_request_id_header_present(self):
        """Test that X-Request-ID header is returned in response."""
        response = client.get("/health", headers={"X-Request-ID": "test-123"})
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"] == "test-123"
    
    def test_request_id_header_generated(self):
        """Test that X-Request-ID header is generated when not provided."""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
        # Should be a UUID
        import uuid
        try:
            uuid.UUID(response.headers["X-Request-ID"])
        except ValueError:
            pytest.fail("X-Request-ID is not a valid UUID")
