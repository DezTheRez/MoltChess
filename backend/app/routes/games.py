"""Game endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal

from ..database import get_db

router = APIRouter()


# IMPORTANT: /games/live must come BEFORE /games/{game_id} to avoid route conflicts
@router.get("/games/live")
async def get_live_games():
    """Get all currently active games."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT g.id, g.category, g.started_at,
                   g.white_agent_id, g.black_agent_id,
                   w.name as white_name, w.avatar_url as white_avatar,
                   w.elo_bullet as white_elo_bullet, w.elo_blitz as white_elo_blitz, w.elo_rapid as white_elo_rapid,
                   b.name as black_name, b.avatar_url as black_avatar,
                   b.elo_bullet as black_elo_bullet, b.elo_blitz as black_elo_blitz, b.elo_rapid as black_elo_rapid
            FROM games g
            JOIN agents w ON g.white_agent_id = w.id
            JOIN agents b ON g.black_agent_id = b.id
            WHERE g.status = 'active'
            ORDER BY g.started_at DESC
            """
        )
        games = await cursor.fetchall()
        
        result = []
        for g in games:
            game_dict = dict(g)
            # Add correct Elo based on category
            category = game_dict["category"]
            game_dict["white_elo"] = game_dict.get(f"white_elo_{category}", 1200)
            game_dict["black_elo"] = game_dict.get(f"black_elo_{category}", 1200)
            result.append(game_dict)
        
        return {
            "success": True,
            "games": result,
        }


@router.get("/games")
async def list_games(
    status: Optional[Literal["pending", "active", "ended"]] = Query(default=None),
    category: Optional[Literal["bullet", "blitz", "rapid"]] = Query(default=None),
    agent_id: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0)
):
    """List games with optional filters."""
    conditions = []
    params = []
    
    if status:
        conditions.append("g.status = ?")
        params.append(status)
    
    if category:
        conditions.append("g.category = ?")
        params.append(category)
    
    if agent_id:
        conditions.append("(g.white_agent_id = ? OR g.black_agent_id = ?)")
        params.extend([agent_id, agent_id])
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    async with get_db() as db:
        # Get total count
        cursor = await db.execute(
            f"""
            SELECT COUNT(*) as count FROM games g WHERE {where_clause}
            """,
            params
        )
        total_row = await cursor.fetchone()
        total = total_row["count"] if total_row else 0
        
        # Get games
        cursor = await db.execute(
            f"""
            SELECT g.id, g.category, g.status, g.result, g.termination,
                   g.started_at, g.ended_at,
                   g.white_agent_id, g.black_agent_id,
                   w.name as white_name, b.name as black_name
            FROM games g
            JOIN agents w ON g.white_agent_id = w.id
            JOIN agents b ON g.black_agent_id = b.id
            WHERE {where_clause}
            ORDER BY g.started_at DESC
            LIMIT ? OFFSET ?
            """,
            params + [limit, offset]
        )
        games = await cursor.fetchall()
        
        return {
            "success": True,
            "total": total,
            "games": [dict(g) for g in games],
        }


@router.get("/games/{game_id}")
async def get_game(game_id: str):
    """Get a game by ID."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT g.*,
                   w.name as white_name, w.avatar_url as white_avatar,
                   b.name as black_name, b.avatar_url as black_avatar
            FROM games g
            JOIN agents w ON g.white_agent_id = w.id
            JOIN agents b ON g.black_agent_id = b.id
            WHERE g.id = ?
            """,
            (game_id,)
        )
        game = await cursor.fetchone()
        
        if not game:
            raise HTTPException(status_code=404, detail="Game not found")
        
        return {
            "success": True,
            "game": dict(game),
        }
