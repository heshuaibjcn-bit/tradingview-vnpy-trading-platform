"""
Core configuration for Energy Storage Investment Decision System
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    APP_NAME: str = "Energy Storage Investment Decision API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ]

    # Supabase Configuration
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Calculation Parameters
    DEFAULT_PROJECT_LIFETIME_YEARS: int = 15
    DEFAULT_DISCOUNT_RATE: float = 0.08  # 8%
    DEFAULT_INFLATION_RATE: float = 0.03  # 3%

    # Report Configuration
    REPORT_FONT: str = "Helvetica"
    REPORT_FONT_SIZE: int = 10
    REPORT_TITLE_SIZE: int = 18

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
