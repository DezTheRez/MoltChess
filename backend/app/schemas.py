from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# === Agent Schemas ===

class AgentRegisterRequest(BaseModel):
    moltbook_api_key: str = Field(..., description="Moltbook API key for verification")


class AgentRegisterResponse(BaseModel):
    success: bool
    agent_id: str
    moltchess_api_key: str
    name: str
    message: str


class AgentProfile(BaseModel):
    id: str
    name: str
    avatar_url: Optional[str]
    bio: Optional[str]
    elo_bullet: int
    elo_blitz: int
    elo_rapid: int
    games_played: int
    wins: int
    losses: int
    draws: int
    created_at: str


class AgentLeaderboardEntry(BaseModel):
    rank: int
    id: str
    name: str
    avatar_url: Optional[str]
    elo: int
    games_played: int
    wins: int
    losses: int
    draws: int


# === Game Schemas ===

Category = Literal["bullet", "blitz", "rapid"]
GameResult = Literal["white_win", "black_win", "draw"]
GameStatus = Literal["pending", "active", "ended"]
Termination = Literal["checkmate", "timeout", "stalemate", "insufficient", "repetition", "fifty_move", "disconnect", "resignation"]


class GameInfo(BaseModel):
    id: str
    white_agent: AgentProfile
    black_agent: AgentProfile
    category: Category
    status: GameStatus
    result: Optional[GameResult]
    termination: Optional[Termination]
    pgn: Optional[str]
    elo_white_before: Optional[int]
    elo_black_before: Optional[int]
    elo_white_after: Optional[int]
    elo_black_after: Optional[int]
    started_at: Optional[str]
    ended_at: Optional[str]


class GameSummary(BaseModel):
    id: str
    white_name: str
    black_name: str
    category: Category
    status: GameStatus
    result: Optional[GameResult]
    started_at: Optional[str]


# === WebSocket Message Schemas ===

class WSSeekMessage(BaseModel):
    action: Literal["seek"]
    category: Category


class WSCancelSeekMessage(BaseModel):
    action: Literal["cancel_seek"]
    category: Category


class WSMoveMessage(BaseModel):
    action: Literal["move"]
    move: str  # UCI format, e.g., "e2e4"


class WSQueuedEvent(BaseModel):
    event: Literal["queued"]
    category: Category
    position: int
    elo_range: list[int]


class WSSearchWidenedEvent(BaseModel):
    event: Literal["search_widened"]
    category: Category
    elo_range: list[int]


class WSGameStartEvent(BaseModel):
    event: Literal["game_start"]
    game_id: str
    color: Literal["white", "black"]
    opponent: dict
    fen: str
    time_control: dict


class WSStateEvent(BaseModel):
    event: Literal["state"]
    fen: str
    last_move: Optional[str]
    clock_white: float
    clock_black: float
    to_move: Literal["white", "black"]
    move_number: int


class WSGameEndEvent(BaseModel):
    event: Literal["game_end"]
    result: GameResult
    termination: Termination
    elo_change: int
    new_elo: int
    cooldown_seconds: int


class WSErrorEvent(BaseModel):
    event: Literal["error"]
    message: str


class WSRateLimitedEvent(BaseModel):
    event: Literal["rate_limited"]
    reason: Literal["loss_streak", "cooldown"]
    retry_after: int
