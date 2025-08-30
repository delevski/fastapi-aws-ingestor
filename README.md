# FastAPI AWS Ingestor

A production-ready FastAPI service that accepts JSON payloads, transforms data, and stores it to AWS S3 or DynamoDB.

## Features

- **REST API**: Accepts JSON payloads via POST `/ingest`
- **Data Validation**: Uses Pydantic v2 for robust input validation
- **Data Transformation**: Adds computed fields (slug, name_upper, value_times_two, received_at, sk)
- **Flexible Storage**: Supports AWS S3 or DynamoDB based on environment configuration
- **Comprehensive Testing**: Unit tests with pytest and moto for AWS services
- **Production Ready**: Robust logging, error handling, and Docker support

## Quick Start

### Prerequisites

- Python 3.11+
- AWS credentials configured (for production use)

### Local Development

1. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   # For S3 storage
   export STORAGE_BACKEND=s3
   export S3_BUCKET=your-bucket-name
   export AWS_REGION=us-east-1
   
   # OR for DynamoDB storage
   export STORAGE_BACKEND=dynamodb
   export DDB_TABLE=your-table-name
   export AWS_REGION=us-east-1
   ```

4. **Run the application:**
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## API Usage

### Example cURL for `/ingest`

```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -H "X-Request-ID: my-request-123" \
  -d '{
    "items": [
      {
        "id": "item-1",
        "name": "Sample Item",
        "value": 15.5,
        "metadata": {"category": "electronics"}
      },
      {
        "id": "item-2",
        "name": "Another Item!",
        "value": 25.0,
        "timestamp": "2024-01-01T12:00:00Z",
        "metadata": {"priority": "high"}
      }
    ]
  }'
```

### Response Format

```json
{
  "stored": 2,
  "keys": [
    "items/item-1-2024-01-15T10:30:00.123456.json",
    "items/item-2-2024-01-15T10:30:00.123457.json"
  ]
}
```

## Testing

Run the test suite:

```bash
pytest -q
```

The tests include:
- **Transform unit tests**: Verify slug, name_upper, value_times_two calculations
- **Validation tests**: Test input validation and error responses
- **S3 storage tests**: Success and failure scenarios with moto
- **DynamoDB storage tests**: Success scenarios with moto
- **Health endpoint tests**: Verify health check functionality
- **Request ID middleware tests**: Test X-Request-ID header handling

## AWS Setup

### S3 Setup

1. Create an S3 bucket:
   ```bash
   aws s3 mb s3://your-bucket-name
   ```

2. Configure bucket permissions as needed for your use case.

### DynamoDB Setup

1. Create a DynamoDB table with PK/SK key schema:
   ```bash
   aws dynamodb create-table \
     --table-name your-table-name \
     --attribute-definitions \
       AttributeName=PK,AttributeType=S \
       AttributeName=SK,AttributeType=S \
     --key-schema \
       AttributeName=PK,KeyType=HASH \
       AttributeName=SK,KeyType=RANGE \
     --billing-mode PAY_PER_REQUEST
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STORAGE_BACKEND` | Storage backend: "s3" or "dynamodb" | "s3" | No |
| `AWS_REGION` | AWS region | "us-east-1" | No |
| `S3_BUCKET` | S3 bucket name | None | Yes (if S3 backend) |
| `DDB_TABLE` | DynamoDB table name | None | Yes (if DynamoDB backend) |
| `LOG_LEVEL` | Logging level | "INFO" | No |
| `SERVICE_NAME` | Service name for logging | "fastapi-aws-ingestor" | No |

## Data Transformation

The service automatically transforms each input item by adding:

- **slug**: URL-friendly version of the name (lowercase, alphanumeric + hyphens)
- **name_upper**: Uppercase version of the name
- **value_times_two**: Original value multiplied by 2
- **received_at**: Current UTC timestamp when item was received
- **sk**: Sort key string (ISO format of received_at)

## Logging and Error Handling

- **Structured logging** with timestamps and log levels
- **Request ID tracking** via X-Request-ID header
- **Global exception handling** with proper HTTP status codes
- **AWS error handling** with detailed error messages
- **Graceful degradation** on storage failures

## Docker

### Build and Run

```bash
# Build the image
docker build -t fastapi-aws-ingestor .

# Run with environment variables
docker run -p 8000:8000 \
  -e STORAGE_BACKEND=s3 \
  -e S3_BUCKET=your-bucket \
  -e AWS_REGION=us-east-1 \
  fastapi-aws-ingestor
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - STORAGE_BACKEND=s3
      - S3_BUCKET=your-bucket
      - AWS_REGION=us-east-1
      - LOG_LEVEL=INFO
```

## Project Structure

```
fastapi-aws-ingestor/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Environment configuration
│   ├── schemas.py           # Pydantic data models
│   ├── transform.py         # Data transformation logic
│   ├── storage.py           # AWS storage implementations
│   └── main.py              # FastAPI application
├── tests/
│   └── test_app.py          # Comprehensive test suite
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
└── README.md               # This file
```

## Development

### Code Standards

- **Type hints** throughout the codebase
- **Small, focused functions** with clear names
- **Robust error handling** around AWS operations
- **No unused code** or imports
- **Standard library → third-party → local** import order
- **Pydantic v2 APIs** for data validation

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_app.py::TestTransform

# Run with verbose output
pytest -v
```

## License

This project is licensed under the MIT License.
