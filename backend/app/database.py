import aiosqlite
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

DATABASE_PATH = os.getenv("DATABASE_PATH", "moltchess.db")


async def init_db():
    """Initialize database with schema."""
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                avatar_url TEXT,
                bio TEXT,
                moltbook_key_hash TEXT NOT NULL,
                moltchess_api_key TEXT NOT NULL UNIQUE,
                elo_bullet INTEGER DEFAULT 1200,
                elo_blitz INTEGER DEFAULT 1200,
                elo_rapid INTEGER DEFAULT 1200,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                loss_streak_bullet INTEGER DEFAULT 0,
                loss_streak_blitz INTEGER DEFAULT 0,
                loss_streak_rapid INTEGER DEFAULT 0,
                last_game_ended_at TEXT,
                cooldown_until TEXT,
                created_at TEXT NOT NULL,
                moltbook_synced_at TEXT
            );
            
            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                white_agent_id TEXT NOT NULL,
                black_agent_id TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                result TEXT,
                termination TEXT,
                pgn TEXT,
                elo_white_before INTEGER,
                elo_black_before INTEGER,
                elo_white_after INTEGER,
                elo_black_after INTEGER,
                time_white_remaining REAL,
                time_black_remaining REAL,
                started_at TEXT,
                ended_at TEXT,
                FOREIGN KEY (white_agent_id) REFERENCES agents(id),
                FOREIGN KEY (black_agent_id) REFERENCES agents(id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
            CREATE INDEX IF NOT EXISTS idx_games_category ON games(category);
            CREATE INDEX IF NOT EXISTS idx_agents_elo_bullet ON agents(elo_bullet);
            CREATE INDEX IF NOT EXISTS idx_agents_elo_blitz ON agents(elo_blitz);
            CREATE INDEX IF NOT EXISTS idx_agents_elo_rapid ON agents(elo_rapid);
        """)
        await db.commit()


@asynccontextmanager
async def get_db() -> AsyncGenerator[aiosqlite.Connection, None]:
    """Get database connection."""
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()
