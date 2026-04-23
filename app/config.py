from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./rental_system.db"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # App
    APP_NAME: str = "Rental Management System"
    DEBUG: bool = True
    FRONTEND_ENABLED: bool = True

    # Bootstrap admin (created on first run if no users exist)
    DEFAULT_ADMIN_EMAIL: str = "admin@rental.com"
    DEFAULT_ADMIN_PASSWORD: str = "admin123"

    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
