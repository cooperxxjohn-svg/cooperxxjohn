"""
Configuration Management for Painting.ai
Centralized environment variable loading and validation
Supports dev/staging/production environments
"""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

Environment = Literal["development", "staging", "production"]


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = Field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            "postgresql://paintingai:changeme123@localhost:5432/paintingai"
        ),
        description="PostgreSQL connection URL"
    )
    pool_size: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "20")),
        description="Connection pool size"
    )
    max_overflow: int = Field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "10")),
        description="Max overflow connections"
    )
    pool_timeout: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_TIMEOUT", "30")),
        description="Pool timeout in seconds"
    )
    pool_recycle: int = Field(
        default_factory=lambda: int(os.getenv("DB_POOL_RECYCLE", "3600")),
        description="Connection recycle time in seconds"
    )

    @validator("url")
    def validate_url(cls, v):
        if not v:
            raise ValueError("DATABASE_URL is required")
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v


class RedisConfig(BaseModel):
    """Redis configuration"""
    url: str = Field(
        default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        description="Redis connection URL"
    )
    password: Optional[str] = Field(
        default_factory=lambda: os.getenv("REDIS_PASSWORD"),
        description="Redis password"
    )
    session_db: int = Field(
        default_factory=lambda: int(os.getenv("REDIS_SESSION_DB", "1")),
        description="Redis database for sessions"
    )
    cache_db: int = Field(
        default_factory=lambda: int(os.getenv("REDIS_CACHE_DB", "2")),
        description="Redis database for cache"
    )


class S3Config(BaseModel):
    """AWS S3 configuration"""
    access_key_id: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_ACCESS_KEY_ID"),
        description="AWS access key ID"
    )
    secret_access_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_SECRET_ACCESS_KEY"),
        description="AWS secret access key"
    )
    region: str = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1"),
        description="AWS region"
    )
    bucket_uploads: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_S3_BUCKET_UPLOADS"),
        description="S3 bucket for file uploads"
    )
    bucket_exports: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_S3_BUCKET_EXPORTS"),
        description="S3 bucket for exports"
    )
    signed_url_expiry: int = Field(
        default_factory=lambda: int(os.getenv("S3_SIGNED_URL_EXPIRY", "86400")),
        description="Signed URL expiration in seconds (default: 24 hours)"
    )
    enabled: bool = Field(
        default_factory=lambda: os.getenv("S3_ENABLED", "false").lower() == "true",
        description="Enable S3 storage (fallback to local if False)"
    )

    def is_configured(self) -> bool:
        """Check if S3 is fully configured"""
        return all([
            self.enabled,
            self.access_key_id,
            self.secret_access_key,
            self.bucket_uploads,
            self.bucket_exports
        ])


class StripeConfig(BaseModel):
    """Stripe payment configuration"""
    secret_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("STRIPE_SECRET_KEY"),
        description="Stripe secret key"
    )
    webhook_secret: Optional[str] = Field(
        default_factory=lambda: os.getenv("STRIPE_WEBHOOK_SECRET"),
        description="Stripe webhook secret"
    )
    price_starter: Optional[str] = Field(
        default_factory=lambda: os.getenv("STRIPE_PRICE_STARTER"),
        description="Stripe price ID for Starter plan"
    )
    price_pro: Optional[str] = Field(
        default_factory=lambda: os.getenv("STRIPE_PRICE_PRO"),
        description="Stripe price ID for Pro plan"
    )
    price_enterprise: Optional[str] = Field(
        default_factory=lambda: os.getenv("STRIPE_PRICE_ENTERPRISE"),
        description="Stripe price ID for Enterprise plan"
    )

    def is_configured(self) -> bool:
        """Check if Stripe is fully configured"""
        return bool(self.secret_key)


class EmailConfig(BaseModel):
    """Email service configuration"""
    sendgrid_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("SENDGRID_API_KEY"),
        description="SendGrid API key"
    )
    from_email: str = Field(
        default_factory=lambda: os.getenv("FROM_EMAIL", "noreply@paintingai.com"),
        description="From email address"
    )

    def is_configured(self) -> bool:
        """Check if email is fully configured"""
        return bool(self.sendgrid_api_key)


class AIConfig(BaseModel):
    """AI service configuration"""
    anthropic_api_key: str = Field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""),
        description="Anthropic API key for Claude"
    )

    @validator("anthropic_api_key")
    def validate_api_key(cls, v):
        if not v:
            raise ValueError("ANTHROPIC_API_KEY is required")
        return v


class SecurityConfig(BaseModel):
    """Security configuration"""
    secret_key: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", ""),
        description="Secret key for JWT tokens"
    )
    frontend_url: str = Field(
        default_factory=lambda: os.getenv("FRONTEND_URL", "http://localhost:3000"),
        description="Frontend URL for CORS"
    )

    @validator("secret_key")
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError("SECRET_KEY is required")
        if len(v) < 32:
            logger.warning("SECRET_KEY should be at least 32 characters for security")
        return v


class MonitoringConfig(BaseModel):
    """Monitoring and logging configuration"""
    sentry_dsn: Optional[str] = Field(
        default_factory=lambda: os.getenv("SENTRY_DSN"),
        description="Sentry DSN for error tracking"
    )
    log_level: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level"
    )

    def is_configured(self) -> bool:
        """Check if monitoring is configured"""
        return bool(self.sentry_dsn)


class Config(BaseModel):
    """Main application configuration"""

    # Environment
    environment: Environment = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="Application environment"
    )

    # Service configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    s3: S3Config = Field(default_factory=S3Config)
    stripe: StripeConfig = Field(default_factory=StripeConfig)
    email: EmailConfig = Field(default_factory=EmailConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)

    # Server settings
    host: str = Field(
        default_factory=lambda: os.getenv("HOST", "0.0.0.0"),
        description="Server host"
    )
    port: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "8000")),
        description="Server port"
    )

    # Feature flags
    enable_payments: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_PAYMENTS", "true").lower() == "true",
        description="Enable payment features"
    )
    enable_public_api: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_PUBLIC_API", "true").lower() == "true",
        description="Enable public API"
    )

    class Config:
        case_sensitive = False

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def validate_required(self):
        """
        Validate all required configuration is present
        Raises ValueError if critical config is missing
        """
        errors = []

        # Always required
        if not self.ai.anthropic_api_key:
            errors.append("ANTHROPIC_API_KEY is required")

        if not self.security.secret_key:
            errors.append("SECRET_KEY is required")

        if not self.database.url:
            errors.append("DATABASE_URL is required")

        # Production requirements
        if self.is_production():
            if not self.s3.is_configured():
                errors.append("S3 configuration is required in production (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_S3_BUCKET_UPLOADS, AWS_S3_BUCKET_EXPORTS)")

            if self.enable_payments and not self.stripe.is_configured():
                errors.append("Stripe configuration is required when payments are enabled (STRIPE_SECRET_KEY)")

            if not self.monitoring.is_configured():
                logger.warning("Monitoring not configured for production (SENTRY_DSN)")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

        logger.info(f"Configuration validated for {self.environment} environment")

    def get_summary(self) -> dict:
        """Get configuration summary (safe for logging, no secrets)"""
        return {
            "environment": self.environment,
            "database": {
                "connected": bool(self.database.url),
                "pool_size": self.database.pool_size
            },
            "redis": {
                "configured": bool(self.redis.url)
            },
            "s3": {
                "enabled": self.s3.enabled,
                "configured": self.s3.is_configured(),
                "region": self.s3.region
            },
            "stripe": {
                "enabled": self.enable_payments,
                "configured": self.stripe.is_configured()
            },
            "email": {
                "configured": self.email.is_configured()
            },
            "monitoring": {
                "configured": self.monitoring.is_configured()
            },
            "features": {
                "payments": self.enable_payments,
                "public_api": self.enable_public_api
            }
        }


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance
    Creates and validates on first call
    """
    global _config
    if _config is None:
        _config = Config()
        _config.validate_required()
        logger.info("Configuration loaded and validated")
    return _config


def reload_config():
    """
    Reload configuration from environment
    Useful for testing or dynamic config updates
    """
    global _config
    _config = None
    load_dotenv(override=True)
    return get_config()


if __name__ == "__main__":
    # Test configuration
    logging.basicConfig(level=logging.INFO)

    try:
        config = get_config()
        print("\n" + "="*60)
        print("PAINTING.AI CONFIGURATION")
        print("="*60)

        summary = config.get_summary()

        print(f"\nEnvironment: {config.environment}")
        print(f"Host: {config.host}:{config.port}")

        print("\nDatabase:")
        print(f"  Connected: {summary['database']['connected']}")
        print(f"  Pool Size: {summary['database']['pool_size']}")

        print("\nRedis:")
        print(f"  Configured: {summary['redis']['configured']}")

        print("\nS3 Storage:")
        print(f"  Enabled: {summary['s3']['enabled']}")
        print(f"  Configured: {summary['s3']['configured']}")
        print(f"  Region: {summary['s3']['region']}")

        print("\nPayments (Stripe):")
        print(f"  Enabled: {summary['stripe']['enabled']}")
        print(f"  Configured: {summary['stripe']['configured']}")

        print("\nEmail:")
        print(f"  Configured: {summary['email']['configured']}")

        print("\nMonitoring:")
        print(f"  Configured: {summary['monitoring']['configured']}")

        print("\nFeatures:")
        print(f"  Payments: {summary['features']['payments']}")
        print(f"  Public API: {summary['features']['public_api']}")

        print("\n" + "="*60)
        print("✅ Configuration valid!")
        print("="*60 + "\n")

    except ValueError as e:
        print("\n" + "="*60)
        print("❌ CONFIGURATION ERROR")
        print("="*60)
        print(f"\n{e}\n")
        print("Please set required environment variables in .env file")
        print("="*60 + "\n")
        exit(1)
