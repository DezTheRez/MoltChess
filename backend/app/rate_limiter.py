"""Rate limiting for post-game cooldowns and loss streak backoff."""

import time
from dataclasses import dataclass
from typing import Optional, Dict
from datetime import datetime, timedelta


@dataclass
class AgentRateLimitState:
    """Tracks rate limit state for an agent."""
    agent_id: str
    
    # Cooldowns (timestamp when cooldown ends)
    cooldown_bullet: Optional[float] = None
    cooldown_blitz: Optional[float] = None
    cooldown_rapid: Optional[float] = None
    
    # Loss streaks
    loss_streak_bullet: int = 0
    loss_streak_blitz: int = 0
    loss_streak_rapid: int = 0
    
    def get_cooldown(self, category: str) -> Optional[float]:
        """Get cooldown end time for a category."""
        return getattr(self, f"cooldown_{category}", None)
    
    def set_cooldown(self, category: str, until: float):
        """Set cooldown end time for a category."""
        setattr(self, f"cooldown_{category}", until)
    
    def get_loss_streak(self, category: str) -> int:
        """Get loss streak for a category."""
        return getattr(self, f"loss_streak_{category}", 0)
    
    def set_loss_streak(self, category: str, streak: int):
        """Set loss streak for a category."""
        setattr(self, f"loss_streak_{category}", streak)
    
    def increment_loss_streak(self, category: str):
        """Increment loss streak for a category."""
        current = self.get_loss_streak(category)
        self.set_loss_streak(category, current + 1)
    
    def reset_loss_streak(self, category: str):
        """Reset loss streak for a category (on win or draw)."""
        self.set_loss_streak(category, 0)


class RateLimiter:
    """Manages rate limits for all agents."""
    
    # Cooldown durations per category (seconds)
    COOLDOWNS = {
        "bullet": 30,
        "blitz": 60,
        "rapid": 120,
    }
    
    # Loss streak settings
    LOSS_STREAK_THRESHOLD = 3
    LOSS_STREAK_ADDITIONAL_COOLDOWN = 120  # 2 minutes
    
    def __init__(self):
        self.states: Dict[str, AgentRateLimitState] = {}
    
    def get_state(self, agent_id: str) -> AgentRateLimitState:
        """Get or create rate limit state for an agent."""
        if agent_id not in self.states:
            self.states[agent_id] = AgentRateLimitState(agent_id=agent_id)
        return self.states[agent_id]
    
    def check_can_seek(self, agent_id: str, category: str) -> tuple[bool, Optional[str], int]:
        """
        Check if an agent can seek a game.
        
        Returns:
            Tuple of (can_seek, reason, retry_after_seconds)
        """
        state = self.get_state(agent_id)
        now = time.time()
        
        # Check cooldown
        cooldown_until = state.get_cooldown(category)
        if cooldown_until and now < cooldown_until:
            retry_after = int(cooldown_until - now)
            return False, "cooldown", retry_after
        
        # Check loss streak
        loss_streak = state.get_loss_streak(category)
        if loss_streak >= self.LOSS_STREAK_THRESHOLD:
            # Additional cooldown for loss streak
            # This is applied on top of the regular cooldown
            # Already handled in apply_game_result
            pass
        
        return True, None, 0
    
    def apply_game_result(
        self,
        agent_id: str,
        category: str,
        is_winner: bool,
        is_draw: bool = False
    ) -> int:
        """
        Apply game result and return total cooldown seconds.
        
        Returns:
            Total cooldown seconds applied
        """
        state = self.get_state(agent_id)
        now = time.time()
        
        # Base cooldown
        base_cooldown = self.COOLDOWNS.get(category, 60)
        total_cooldown = base_cooldown
        
        if is_draw:
            # Draw doesn't affect loss streak
            pass
        elif is_winner:
            # Win resets loss streak
            state.reset_loss_streak(category)
        else:
            # Loss increments streak
            state.increment_loss_streak(category)
            
            # Check for loss streak penalty
            if state.get_loss_streak(category) >= self.LOSS_STREAK_THRESHOLD:
                total_cooldown += self.LOSS_STREAK_ADDITIONAL_COOLDOWN
        
        # Apply cooldown
        cooldown_until = now + total_cooldown
        state.set_cooldown(category, cooldown_until)
        
        return total_cooldown
    
    def get_cooldown_remaining(self, agent_id: str, category: str) -> int:
        """Get remaining cooldown seconds (0 if none)."""
        state = self.get_state(agent_id)
        cooldown_until = state.get_cooldown(category)
        
        if cooldown_until is None:
            return 0
        
        remaining = cooldown_until - time.time()
        return max(0, int(remaining))
    
    def clear_cooldown(self, agent_id: str, category: str):
        """Clear cooldown for testing purposes."""
        state = self.get_state(agent_id)
        state.set_cooldown(category, None)
    
    def get_loss_streak(self, agent_id: str, category: str) -> int:
        """Get current loss streak."""
        return self.get_state(agent_id).get_loss_streak(category)


# Global rate limiter instance
rate_limiter = RateLimiter()
