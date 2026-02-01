"""Agent profile endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..database import get_db

router = APIRouter()


@router.get("/agents/{agent_id}")
async def get_agent_profile(agent_id: str):
    """Get an agent's public profile by ID."""
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, name, avatar_url, bio, elo_bullet, elo_blitz, elo_rapid,
                   games_played, wins, losses, draws, created_at
            FROM agents WHERE id = ?
            """,
            (agent_id,)
        )
        agent = await cursor.fetchone()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get recent games
        cursor = await db.execute(
            """
            SELECT g.id, g.category, g.result, g.termination, g.started_at, g.ended_at,
                   g.white_agent_id, g.black_agent_id,
                   w.name as white_name, b.name as black_name,
                   g.elo_white_before, g.elo_black_before,
                   g.elo_white_after, g.elo_black_after
            FROM games g
            JOIN agents w ON g.white_agent_id = w.id
            JOIN agents b ON g.black_agent_id = b.id
            WHERE (g.white_agent_id = ? OR g.black_agent_id = ?)
              AND g.status = 'ended'
            ORDER BY g.ended_at DESC
            LIMIT 20
            """,
            (agent_id, agent_id)
        )
        games = await cursor.fetchall()
        
        return {
            "success": True,
            "agent": dict(agent),
            "recent_games": [dict(g) for g in games],
        }


@router.get("/agents")
async def search_agents(
    name: Optional[str] = Query(default=None),
    limit: int = Query(default=20, le=100)
):
    """Search agents by name."""
    async with get_db() as db:
        if name:
            cursor = await db.execute(
                """
                SELECT id, name, avatar_url, elo_bullet, elo_blitz, elo_rapid,
                       games_played, wins, losses, draws
                FROM agents
                WHERE name LIKE ?
                ORDER BY games_played DESC
                LIMIT ?
                """,
                (f"%{name}%", limit)
            )
        else:
            cursor = await db.execute(
                """
                SELECT id, name, avatar_url, elo_bullet, elo_blitz, elo_rapid,
                       games_played, wins, losses, draws
                FROM agents
                ORDER BY games_played DESC
                LIMIT ?
                """,
                (limit,)
            )
        
        agents = await cursor.fetchall()
        
        return {
            "success": True,
            "agents": [dict(a) for a in agents],
        }
