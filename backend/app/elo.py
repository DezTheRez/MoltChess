"""Elo rating calculation."""

from typing import Tuple


def calculate_elo_change(
    winner_elo: int,
    loser_elo: int,
    is_draw: bool = False,
    k_factor: int = 32
) -> Tuple[int, int]:
    """
    Calculate Elo changes after a game.
    
    Returns:
        Tuple of (winner_change, loser_change) or (white_change, black_change) for draws
    """
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner
    
    if is_draw:
        # For draws, both players move toward 0.5 expected
        change_higher = round(k_factor * (0.5 - expected_winner))
        change_lower = round(k_factor * (0.5 - expected_loser))
        return change_higher, change_lower
    else:
        # Winner gains, loser loses
        winner_change = round(k_factor * (1 - expected_winner))
        loser_change = round(k_factor * (0 - expected_loser))
        return winner_change, loser_change


def apply_elo_floor(elo: int, floor: int = 100) -> int:
    """Ensure Elo doesn't drop below floor."""
    return max(elo, floor)


def get_elo_band(elo: int) -> str:
    """Get the Elo band for matchmaking."""
    if elo < 1000:
        return "bronze"
    elif elo <= 1400:
        return "silver"
    else:
        return "gold"


def elos_compatible(elo1: int, elo2: int, max_diff: int) -> bool:
    """Check if two Elos are within acceptable range."""
    return abs(elo1 - elo2) <= max_diff
