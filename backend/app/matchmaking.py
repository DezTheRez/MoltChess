"""Matchmaking system with Elo-banded queues and wait-based widening."""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable, Awaitable
from enum import Enum

from .elo import get_elo_band, elos_compatible


class SeekStatus(Enum):
    SEARCHING = "searching"
    WIDENING_1 = "widening_1"  # After 30s, ±400 Elo
    WIDENING_2 = "widening_2"  # After 60s, any Elo
    MATCHED = "matched"
    CANCELLED = "cancelled"


@dataclass
class Seeker:
    agent_id: str
    agent_name: str
    elo: int
    category: str
    band: str
    status: SeekStatus = SeekStatus.SEARCHING
    queued_at: float = field(default_factory=time.time)
    position: int = 0
    
    def get_elo_range(self) -> tuple[int, int]:
        """Get current acceptable Elo range based on status."""
        if self.status == SeekStatus.SEARCHING:
            return (self.elo - 200, self.elo + 200)
        elif self.status == SeekStatus.WIDENING_1:
            return (self.elo - 400, self.elo + 400)
        else:  # WIDENING_2 or later
            return (0, 9999)
    
    def get_wait_time(self) -> float:
        """Get time spent in queue."""
        return time.time() - self.queued_at


@dataclass
class MatchResult:
    seeker1: Seeker
    seeker2: Seeker
    category: str


class MatchmakingQueue:
    """Manages matchmaking queues for all categories."""
    
    def __init__(self):
        # Queues per category
        self.queues: Dict[str, List[Seeker]] = {
            "bullet": [],
            "blitz": [],
            "rapid": [],
        }
        
        # Track seekers by agent_id for quick lookup
        self.seekers_by_agent: Dict[str, Dict[str, Seeker]] = {}  # agent_id -> {category -> Seeker}
        
        # Callback for when a match is found
        self.on_match: Optional[Callable[[MatchResult], Awaitable[None]]] = None
        
        # Callback for widening notifications
        self.on_widening: Optional[Callable[[Seeker, list[int]], Awaitable[None]]] = None
        
        # Background task
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the matchmaking loop."""
        self._running = True
        self._task = asyncio.create_task(self._matchmaking_loop())
    
    async def stop(self):
        """Stop the matchmaking loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def add_seeker(self, agent_id: str, agent_name: str, elo: int, category: str) -> Seeker:
        """Add an agent to the matchmaking queue."""
        band = get_elo_band(elo)
        seeker = Seeker(
            agent_id=agent_id,
            agent_name=agent_name,
            elo=elo,
            category=category,
            band=band,
        )
        
        # Add to queue
        self.queues[category].append(seeker)
        seeker.position = len(self.queues[category])
        
        # Track by agent
        if agent_id not in self.seekers_by_agent:
            self.seekers_by_agent[agent_id] = {}
        self.seekers_by_agent[agent_id][category] = seeker
        
        return seeker
    
    async def remove_seeker(self, agent_id: str, category: str) -> bool:
        """Remove an agent from a specific queue."""
        if agent_id in self.seekers_by_agent:
            if category in self.seekers_by_agent[agent_id]:
                seeker = self.seekers_by_agent[agent_id][category]
                seeker.status = SeekStatus.CANCELLED
                
                # Remove from queue
                if seeker in self.queues[category]:
                    self.queues[category].remove(seeker)
                
                # Remove from tracking
                del self.seekers_by_agent[agent_id][category]
                if not self.seekers_by_agent[agent_id]:
                    del self.seekers_by_agent[agent_id]
                
                return True
        return False
    
    async def remove_all_seeks(self, agent_id: str):
        """Remove agent from all queues."""
        if agent_id in self.seekers_by_agent:
            categories = list(self.seekers_by_agent[agent_id].keys())
            for category in categories:
                await self.remove_seeker(agent_id, category)
    
    def get_seeker(self, agent_id: str, category: str) -> Optional[Seeker]:
        """Get a seeker by agent_id and category."""
        if agent_id in self.seekers_by_agent:
            return self.seekers_by_agent[agent_id].get(category)
        return None
    
    def is_seeking(self, agent_id: str) -> bool:
        """Check if agent is in any queue."""
        return agent_id in self.seekers_by_agent and len(self.seekers_by_agent[agent_id]) > 0
    
    def get_queue_position(self, agent_id: str, category: str) -> int:
        """Get position in queue (1-indexed)."""
        seeker = self.get_seeker(agent_id, category)
        if seeker and seeker in self.queues[category]:
            return self.queues[category].index(seeker) + 1
        return 0
    
    async def _matchmaking_loop(self):
        """Background loop that processes queues and finds matches."""
        while self._running:
            try:
                for category in self.queues:
                    await self._process_queue(category)
                await asyncio.sleep(0.5)  # Check every 500ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Matchmaking error: {e}")
                await asyncio.sleep(1)
    
    async def _process_queue(self, category: str):
        """Process a single category queue."""
        queue = self.queues[category]
        if len(queue) < 2:
            return
        
        now = time.time()
        matches_to_make = []
        
        # Update status based on wait time and check for matches
        for seeker in queue:
            wait_time = seeker.get_wait_time()
            old_status = seeker.status
            
            # Update widening status
            if wait_time >= 60 and seeker.status != SeekStatus.WIDENING_2:
                seeker.status = SeekStatus.WIDENING_2
            elif wait_time >= 30 and seeker.status == SeekStatus.SEARCHING:
                seeker.status = SeekStatus.WIDENING_1
            
            # Notify on status change
            if seeker.status != old_status and self.on_widening:
                elo_range = list(seeker.get_elo_range())
                asyncio.create_task(self.on_widening(seeker, elo_range))
        
        # Find matches (iterate through pairs)
        matched_indices = set()
        for i, seeker1 in enumerate(queue):
            if i in matched_indices:
                continue
            
            for j, seeker2 in enumerate(queue):
                if j <= i or j in matched_indices:
                    continue
                
                if self._can_match(seeker1, seeker2):
                    matches_to_make.append((i, j, seeker1, seeker2))
                    matched_indices.add(i)
                    matched_indices.add(j)
                    break
        
        # Process matches
        for i, j, seeker1, seeker2 in matches_to_make:
            seeker1.status = SeekStatus.MATCHED
            seeker2.status = SeekStatus.MATCHED
            
            # Remove from queue
            self.queues[category] = [s for s in queue if s not in (seeker1, seeker2)]
            
            # Remove from tracking
            for seeker in (seeker1, seeker2):
                if seeker.agent_id in self.seekers_by_agent:
                    if category in self.seekers_by_agent[seeker.agent_id]:
                        del self.seekers_by_agent[seeker.agent_id][category]
                    if not self.seekers_by_agent[seeker.agent_id]:
                        del self.seekers_by_agent[seeker.agent_id]
            
            # Notify
            if self.on_match:
                match = MatchResult(seeker1=seeker1, seeker2=seeker2, category=category)
                asyncio.create_task(self.on_match(match))
    
    def _can_match(self, seeker1: Seeker, seeker2: Seeker) -> bool:
        """Check if two seekers can be matched."""
        # Same agent can't play themselves
        if seeker1.agent_id == seeker2.agent_id:
            return False
        
        # Check Elo compatibility based on both seekers' current ranges
        range1 = seeker1.get_elo_range()
        range2 = seeker2.get_elo_range()
        
        # Both must accept each other's Elo
        if not (range1[0] <= seeker2.elo <= range1[1]):
            return False
        if not (range2[0] <= seeker1.elo <= range2[1]):
            return False
        
        return True
    
    def get_queue_stats(self) -> dict:
        """Get statistics about all queues."""
        return {
            category: {
                "count": len(queue),
                "seekers": [
                    {
                        "agent_name": s.agent_name,
                        "elo": s.elo,
                        "band": s.band,
                        "status": s.status.value,
                        "wait_time": round(s.get_wait_time(), 1),
                    }
                    for s in queue
                ]
            }
            for category, queue in self.queues.items()
        }


# Global matchmaking queue instance
matchmaking = MatchmakingQueue()
