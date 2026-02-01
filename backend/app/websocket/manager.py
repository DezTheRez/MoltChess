"""WebSocket connection manager."""

import asyncio
import json
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket
from dataclasses import dataclass, field


@dataclass
class AgentConnection:
    """Represents a connected agent."""
    agent_id: str
    agent_name: str
    websocket: WebSocket
    current_game_id: Optional[str] = None


@dataclass  
class SpectatorConnection:
    """Represents a spectator watching a game."""
    websocket: WebSocket
    game_id: str


class ConnectionManager:
    """Manages WebSocket connections for agents and spectators."""
    
    def __init__(self):
        # Agent connections: agent_id -> AgentConnection
        self.agents: Dict[str, AgentConnection] = {}
        
        # Spectator connections: game_id -> Set[WebSocket]
        self.spectators: Dict[str, Set[WebSocket]] = {}
        
        # Reverse lookup: websocket -> agent_id (for cleanup)
        self.websocket_to_agent: Dict[WebSocket, str] = {}
    
    async def connect_agent(self, websocket: WebSocket, agent_id: str, agent_name: str) -> AgentConnection:
        """Connect an agent. WebSocket must already be accepted."""
        # Disconnect existing connection if any
        if agent_id in self.agents:
            old_conn = self.agents[agent_id]
            try:
                await old_conn.websocket.close(code=4000, reason="New connection")
            except:
                pass
            if old_conn.websocket in self.websocket_to_agent:
                del self.websocket_to_agent[old_conn.websocket]
        
        conn = AgentConnection(
            agent_id=agent_id,
            agent_name=agent_name,
            websocket=websocket
        )
        self.agents[agent_id] = conn
        self.websocket_to_agent[websocket] = agent_id
        
        return conn
    
    async def disconnect_agent(self, websocket: WebSocket):
        """Disconnect an agent."""
        agent_id = self.websocket_to_agent.get(websocket)
        if agent_id:
            if agent_id in self.agents:
                del self.agents[agent_id]
            del self.websocket_to_agent[websocket]
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[AgentConnection]:
        """Get an agent connection by ID."""
        return self.agents.get(agent_id)
    
    def is_agent_connected(self, agent_id: str) -> bool:
        """Check if an agent is connected."""
        return agent_id in self.agents
    
    async def send_to_agent(self, agent_id: str, message: dict):
        """Send a message to a specific agent."""
        conn = self.agents.get(agent_id)
        if conn:
            try:
                await conn.websocket.send_json(message)
            except Exception as e:
                print(f"Error sending to agent {agent_id}: {e}")
    
    async def connect_spectator(self, websocket: WebSocket, game_id: str):
        """Connect a spectator to a game."""
        await websocket.accept()
        
        if game_id not in self.spectators:
            self.spectators[game_id] = set()
        self.spectators[game_id].add(websocket)
    
    async def disconnect_spectator(self, websocket: WebSocket, game_id: str):
        """Disconnect a spectator from a game."""
        if game_id in self.spectators:
            self.spectators[game_id].discard(websocket)
            if not self.spectators[game_id]:
                del self.spectators[game_id]
    
    def get_spectator_count(self, game_id: str) -> int:
        """Get the number of spectators for a game."""
        return len(self.spectators.get(game_id, set()))
    
    async def broadcast_to_spectators(self, game_id: str, message: dict):
        """Broadcast a message to all spectators of a game."""
        spectator_set = self.spectators.get(game_id, set())
        dead_connections = []
        
        for ws in spectator_set:
            try:
                await ws.send_json(message)
            except Exception:
                dead_connections.append(ws)
        
        # Clean up dead connections
        for ws in dead_connections:
            spectator_set.discard(ws)
    
    async def broadcast_to_game(self, game_id: str, message: dict, white_id: str, black_id: str):
        """Broadcast a message to both players and all spectators of a game."""
        # Send to players
        await self.send_to_agent(white_id, message)
        await self.send_to_agent(black_id, message)
        
        # Send to spectators
        await self.broadcast_to_spectators(game_id, message)
    
    def set_agent_game(self, agent_id: str, game_id: Optional[str]):
        """Set the current game for an agent."""
        conn = self.agents.get(agent_id)
        if conn:
            conn.current_game_id = game_id
    
    def get_agent_game(self, agent_id: str) -> Optional[str]:
        """Get the current game for an agent."""
        conn = self.agents.get(agent_id)
        return conn.current_game_id if conn else None


# Global connection manager instance
manager = ConnectionManager()
