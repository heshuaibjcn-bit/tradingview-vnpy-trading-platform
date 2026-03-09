"""
StockAutoTrader - Configuration Management Module
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "StockAutoTrader"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # WebSocket
    WS_PORT: int = 8765
    WS_HOST: str = "localhost"

    # Trading
    TRADING_PASSWORD: str = ""
    MAX_POSITION_RATIO: float = Field(default=0.3, ge=0, le=1)
    MAX_DAILY_LOSS_RATIO: float = Field(default=0.05, ge=0, le=1)

    # Risk Control
    ENABLE_RISK_CONTROL: bool = True
    STOP_LOSS_RATIO: float = Field(default=0.05, ge=0, le=1)
    TAKE_PROFIT_RATIO: float = Field(default=0.10, ge=0, le=1)
    MAX_TRADES_PER_DAY: int = Field(default=10, ge=0)

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_FILE: str = "logs/trading.log"

    # Market Data
    MARKET_DATA_SOURCE: Literal["ths", "api", "both"] = "both"
    ENABLE_THS_DATA: bool = True
    ENABLE_API_DATA: bool = True

    # Automation
    AUTO_LOGIN: bool = False
    AUTO_CONFIRM: bool = False
    SCREENSHOT_PATH: str = "screenshots"

    # Paths
    BASE_DIR: Path = Field(default_factory=lambda: Path(__file__).parent.parent)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @property
    def log_path(self) -> Path:
        """Get log file path"""
        return self.BASE_DIR / self.LOG_FILE

    @property
    def screenshot_path(self) -> Path:
        """Get screenshot directory path"""
        path = self.BASE_DIR / self.SCREENSHOT_PATH
        path.mkdir(parents=True, exist_ok=True)
        return path


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings
