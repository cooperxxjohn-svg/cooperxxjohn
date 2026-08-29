"""
Health check endpoint for database and Redis connections
Used by Docker health checks and monitoring
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    Returns status of database and Redis connections
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    # Check PostgreSQL
    try:
        from database_service import db
        pool_status = db.get_pool_status()

        health_status["services"]["postgresql"] = {
            "status": "healthy",
            "pool_size": pool_status["pool_size"],
            "checked_out": pool_status["checked_out"],
            "checked_in": pool_status["checked_in"]
        }
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        health_status["services"]["postgresql"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Check Redis
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)
        r.ping()

        health_status["services"]["redis"] = {
            "status": "healthy",
            "connected": True
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Return appropriate status code
    if health_status["status"] == "healthy":
        return health_status
    else:
        raise HTTPException(status_code=503, detail=health_status)


@router.get("/health/database")
async def database_health():
    """
    Detailed database health check
    """
    try:
        from database_service import db
        from sqlalchemy import text

        # Test query
        with db.get_session() as session:
            result = session.execute(text("SELECT 1"))
            result.fetchone()

        pool_status = db.get_pool_status()

        return {
            "status": "healthy",
            "database": "postgresql",
            "pool": pool_status,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "error": str(e)}
        )


@router.get("/health/redis")
async def redis_health():
    """
    Detailed Redis health check
    """
    try:
        import redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        r = redis.from_url(redis_url)

        # Test connection
        r.ping()

        # Get info
        info = r.info()

        return {
            "status": "healthy",
            "version": info.get("redis_version"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={"status": "unhealthy", "error": str(e)}
        )
