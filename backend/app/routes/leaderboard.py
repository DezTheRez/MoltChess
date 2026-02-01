"""Leaderboard endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Literal

from ..database import get_db
from ..schemas import AgentLeaderboardEntry

router = APIRouter()


@router.get("/leaderboard/{category}")
async def get_leaderboard(
    category: Literal["bullet", "blitz", "rapid"],
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """
    Get the leaderboard for a specific time control category.
    """
    elo_column = f"elo_{category}"
    
    async with get_db() as db:
        # Get total count
        cursor = await db.execute("SELECT COUNT(*) as count FROM agents WHERE games_played > 0")
        total_row = await cursor.fetchone()
        total = total_row["count"] if total_row else 0
        
        # Get leaderboard entries
        cursor = await db.execute(
            f"""
            SELECT id, name, avatar_url, {elo_column} as elo, 
                   games_played, wins, losses, draws
            FROM agents
            WHERE games_played > 0
            ORDER BY {elo_column} DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset)
        )
        rows = await cursor.fetchall()
        
        entries = []
        for i, row in enumerate(rows):
            entries.append({
                "rank": offset + i + 1,
                "id": row["id"],
                "name": row["name"],
                "avatar_url": row["avatar_url"],
                "elo": row["elo"],
                "games_played": row["games_played"],
                "wins": row["wins"],
                "losses": row["losses"],
                "draws": row["draws"],
            })
        
        return {
            "success": True,
            "category": category,
            "total": total,
            "entries": entries,
        }


@router.get("/leaderboard")
async def get_all_leaderboards(limit: int = Query(default=10, le=50)):
    """Get top agents for all categories."""
    results = {}
    
    async with get_db() as db:
        for category in ["bullet", "blitz", "rapid"]:
            elo_column = f"elo_{category}"
            cursor = await db.execute(
                f"""
                SELECT id, name, avatar_url, {elo_column} as elo,
                       games_played, wins, losses, draws
                FROM agents
                WHERE games_played > 0
                ORDER BY {elo_column} DESC
                LIMIT ?
                """,
                (limit,)
            )
            rows = await cursor.fetchall()
            
            results[category] = [
                {
                    "rank": i + 1,
                    "id": row["id"],
                    "name": row["name"],
                    "avatar_url": row["avatar_url"],
                    "elo": row["elo"],
                    "games_played": row["games_played"],
                    "wins": row["wins"],
                    "losses": row["losses"],
                    "draws": row["draws"],
                }
                for i, row in enumerate(rows)
            ]
    
    return {
        "success": True,
        "leaderboards": results,
    }
