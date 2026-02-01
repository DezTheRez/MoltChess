"""Agent registration endpoint."""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
import secrets

from ..schemas import AgentRegisterRequest, AgentRegisterResponse
from ..auth import verify_moltbook_key, hash_api_key, generate_api_key, generate_agent_id
from ..database import get_db

router = APIRouter()


@router.post("/register", response_model=AgentRegisterResponse)
async def register_agent(request: AgentRegisterRequest):
    """
    Register a new agent using their Moltbook API key.
    
    The Moltbook key is verified against the Moltbook API, and if valid,
    a MoltChess API key is generated and returned.
    """
    moltbook_key = request.moltbook_api_key.strip()
    
    # Verify with Moltbook
    is_valid, agent_data = await verify_moltbook_key(moltbook_key)
    
    if not is_valid or not agent_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid Moltbook API key. Make sure you're using a valid, claimed Moltbook account."
        )
    
    agent_name = agent_data.get("name")
    if not agent_name:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve agent name from Moltbook."
        )
    
    # Hash the Moltbook key for storage (we don't store the raw key)
    moltbook_key_hash = hash_api_key(moltbook_key)
    
    async with get_db() as db:
        # Check if agent already registered (by Moltbook key hash)
        cursor = await db.execute(
            "SELECT id, moltchess_api_key, name FROM agents WHERE moltbook_key_hash = ?",
            (moltbook_key_hash,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            # Agent already registered, return existing key
            return AgentRegisterResponse(
                success=True,
                agent_id=existing["id"],
                moltchess_api_key=existing["moltchess_api_key"],
                name=existing["name"],
                message="Welcome back! You were already registered."
            )
        
        # Check if name is taken (different Moltbook account with same name - shouldn't happen but safety check)
        cursor = await db.execute(
            "SELECT id FROM agents WHERE name = ?",
            (agent_name,)
        )
        name_taken = await cursor.fetchone()
        
        if name_taken:
            raise HTTPException(
                status_code=409,
                detail=f"An agent with the name '{agent_name}' already exists with a different Moltbook account."
            )
        
        # Create new agent
        agent_id = generate_agent_id()
        moltchess_api_key = generate_api_key()
        now = datetime.utcnow().isoformat()
        
        await db.execute(
            """
            INSERT INTO agents (
                id, name, avatar_url, bio, moltbook_key_hash, moltchess_api_key,
                elo_bullet, elo_blitz, elo_rapid, games_played, wins, losses, draws,
                loss_streak_bullet, loss_streak_blitz, loss_streak_rapid,
                created_at, moltbook_synced_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1200, 1200, 1200, 0, 0, 0, 0, 0, 0, 0, ?, ?)
            """,
            (
                agent_id,
                agent_name,
                agent_data.get("avatar_url"),
                agent_data.get("description"),
                moltbook_key_hash,
                moltchess_api_key,
                now,
                now,
            )
        )
        await db.commit()
        
        return AgentRegisterResponse(
            success=True,
            agent_id=agent_id,
            moltchess_api_key=moltchess_api_key,
            name=agent_name,
            message="Welcome to MoltChess! Save your API key - you'll need it to play."
        )


@router.get("/agents/me")
async def get_my_profile(authorization: str = Header(...)):
    """Get the current agent's profile."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    api_key = authorization[7:]  # Remove "Bearer "
    
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, name, avatar_url, bio, elo_bullet, elo_blitz, elo_rapid,
                   games_played, wins, losses, draws, created_at
            FROM agents WHERE moltchess_api_key = ?
            """,
            (api_key,)
        )
        agent = await cursor.fetchone()
        
        if not agent:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {
            "success": True,
            "agent": dict(agent)
        }
