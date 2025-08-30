import logging
import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.schemas import DataBatch
from app.storage import Storage, get_storage_from_env, StorageError
from app.transform import transform_item

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s %(levelname)s %(name)s %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FastAPI AWS Ingestor",
    version="1.0.0"
)


class RequestIDMiddleware:
    """Middleware to handle X-Request-ID header."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope, receive)
            request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
            
            # Add request ID to scope for logging
            scope["request_id"] = request_id
            
            # Create response wrapper to add X-Request-ID header
            async def send_with_request_id(message):
                if message["type"] == "http.response.start":
                    message["headers"].append((b"X-Request-ID", request_id.encode()))
                await send(message)
            
            await self.app(scope, receive, send_with_request_id)
        else:
            await self.app(scope, receive, send)


app.add_middleware(RequestIDMiddleware)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    settings = get_settings()
    return {
        "status": "ok",
        "storage_backend": settings.storage_backend,
        "region": settings.aws_region
    }


def get_storage() -> Storage:
    """Dependency to get storage backend."""
    try:
        return get_storage_from_env()
    except StorageError as e:
        logger.error(f"Storage configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")


@app.post("/ingest", status_code=201)
async def ingest_data(
    data_batch: DataBatch,
    storage: Annotated[Storage, Depends(get_storage)]
):
    """Ingest data batch and store to configured backend."""
    
    try:
        # Transform each item
        transformed_items = [transform_item(item) for item in data_batch.items]
        
        # Store items
        keys = storage.store_batch(transformed_items)
        
        logger.info(f"Successfully ingested {len(transformed_items)} items")
        
        return {
            "stored": len(transformed_items),
            "keys": keys
        }
        
    except StorageError as e:
        logger.error(f"Storage error during ingest: {e}")
        raise HTTPException(status_code=500, detail=f"Storage error: {e}")
    except Exception as e:
        logger.exception(f"Unexpected error during ingest: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
