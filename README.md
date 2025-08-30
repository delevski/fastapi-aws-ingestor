# fastapi-aws-ingestor
A production-ready FastAPI service that:   - Accepts JSON via REST (`POST /ingest`) - Validates &amp; **transforms** the payload - Stores data in **AWS S3** or **DynamoDB** (select via env var) - Includes **3+ meaningful unit tests** (S3 + DynamoDB + validation + transform) - **Bonus**: Dockerfile, logging, and exception handling best practices
