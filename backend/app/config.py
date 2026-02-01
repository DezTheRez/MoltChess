from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "MoltChess"
    debug: bool = False
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./moltchess.db"
    
    # Moltbook
    moltbook_api_base: str = "https://www.moltbook.com/api/v1"
    moltbook_api_key: str = ""  # For testing
    
    # Time controls (seconds)
    time_bullet_base: int = 120  # 2 min
    time_bullet_increment: int = 1
    time_blitz_base: int = 180  # 3 min
    time_blitz_increment: int = 2
    time_rapid_base: int = 600  # 10 min
    time_rapid_increment: int = 5
    
    # Matchmaking
    elo_starting: int = 1200
    elo_floor: int = 100
    elo_band_bronze_max: int = 999
    elo_band_silver_max: int = 1400
    
    # Rate limits (seconds)
    cooldown_bullet: int = 30
    cooldown_blitz: int = 60
    cooldown_rapid: int = 120
    loss_streak_threshold: int = 3
    loss_streak_cooldown: int = 120
    
    # Disconnect
    disconnect_forfeit_time: int = 120  # 2 minutes
    
    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "https://moltchess.io"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
