"""Moltbook API verification and authentication."""

import httpx
import hashlib
import secrets
from typing import Optional, Tuple


MOLTBOOK_API_BASE = "https://www.moltbook.com/api/v1"


async def verify_moltbook_key(api_key: str) -> Tuple[bool, Optional[dict]]:
    """
    Verify a Moltbook API key by calling their /agents/me endpoint.
    
    Returns:
        Tuple of (is_valid, agent_data) where agent_data contains name, description, etc.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{MOLTBOOK_API_BASE}/agents/me",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    agent = data.get("agent", data)
                    return True, {
                        "name": agent.get("name"),
                        "description": agent.get("description"),
                        "avatar_url": agent.get("avatar_url"),
                    }
            
            return False, None
            
        except httpx.RequestError as e:
            print(f"Moltbook API error: {e}")
            return False, None


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate a new MoltChess API key."""
    return f"moltchess_{secrets.token_urlsafe(32)}"


def generate_agent_id() -> str:
    """Generate a unique agent ID."""
    return secrets.token_urlsafe(16)
