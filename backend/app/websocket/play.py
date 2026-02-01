"""WebSocket handler for agent gameplay."""

import asyncio
import json
import random
import time
from typing import Optional, Dict
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from .manager import manager
from ..matchmaking import matchmaking, MatchResult, Seeker
from ..game_engine import ChessGame, GameStatus, GameResult, Termination
from ..rate_limiter import rate_limiter
from ..elo import calculate_elo_change, apply_elo_floor
from ..database import get_db


# Active games: game_id -> ChessGame
active_games: Dict[str, ChessGame] = {}

# Disconnect monitoring task
disconnect_monitor_task: Optional[asyncio.Task] = None


async def authenticate_agent(websocket: WebSocket) -> Optional[dict]:
    """Authenticate agent from WebSocket headers or first message."""
    # Try to get API key from query params or headers
    api_key = websocket.query_params.get("api_key")
    
    if not api_key:
        # Wait for auth message
        try:
            data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
            if data.get("action") == "auth":
                api_key = data.get("api_key")
        except asyncio.TimeoutError:
            return None
    
    if not api_key:
        return None
    
    # Verify API key
    async with get_db() as db:
        cursor = await db.execute(
            """
            SELECT id, name, elo_bullet, elo_blitz, elo_rapid
            FROM agents WHERE moltchess_api_key = ?
            """,
            (api_key,)
        )
        agent = await cursor.fetchone()
        
        if agent:
            return dict(agent)
    
    return None


async def handle_seek(agent_id: str, agent_name: str, category: str, elo: int) -> dict:
    """Handle a seek request."""
    # Check rate limit
    can_seek, reason, retry_after = rate_limiter.check_can_seek(agent_id, category)
    if not can_seek:
        return {
            "event": "rate_limited",
            "reason": reason,
            "retry_after": retry_after
        }
    
    # Check if already in a game
    if manager.get_agent_game(agent_id):
        return {
            "event": "error",
            "message": "You are already in a game"
        }
    
    # Check if already seeking this category
    if matchmaking.get_seeker(agent_id, category):
        return {
            "event": "error",
            "message": f"Already seeking {category}"
        }
    
    # Add to queue
    seeker = await matchmaking.add_seeker(agent_id, agent_name, elo, category)
    
    return {
        "event": "queued",
        "category": category,
        "position": seeker.position,
        "elo_range": list(seeker.get_elo_range())
    }


async def handle_cancel_seek(agent_id: str, category: str) -> dict:
    """Handle a cancel seek request."""
    removed = await matchmaking.remove_seeker(agent_id, category)
    
    if removed:
        return {
            "event": "seek_cancelled",
            "category": category
        }
    else:
        return {
            "event": "error",
            "message": f"Not seeking {category}"
        }


async def handle_move(agent_id: str, move: str) -> Optional[dict]:
    """Handle a move request. Returns error dict if move fails, None on success."""
    game_id = manager.get_agent_game(agent_id)
    if not game_id or game_id not in active_games:
        return {
            "event": "error",
            "message": "You are not in a game"
        }
    
    game = active_games[game_id]
    
    # Check if it's this agent's turn
    if not game.is_agent_turn(agent_id):
        return {
            "event": "error",
            "message": "Not your turn"
        }
    
    # Make the move
    success, error = game.make_move(move)
    
    if not success:
        return {
            "event": "error",
            "message": error or "Invalid move"
        }
    
    # Broadcast state update
    state = game.get_state_dict()
    state["event"] = "state"
    
    await manager.broadcast_to_game(
        game_id, state,
        game.white_agent_id, game.black_agent_id
    )
    
    # Check if game ended
    if game.status == GameStatus.ENDED:
        await end_game(game)
    
    return None


async def create_game(match: MatchResult):
    """Create a new game from a match."""
    import secrets
    
    game_id = secrets.token_urlsafe(12)
    
    # Randomly assign colors
    if random.random() < 0.5:
        white_id, white_name, white_elo = match.seeker1.agent_id, match.seeker1.agent_name, match.seeker1.elo
        black_id, black_name, black_elo = match.seeker2.agent_id, match.seeker2.agent_name, match.seeker2.elo
    else:
        white_id, white_name, white_elo = match.seeker2.agent_id, match.seeker2.agent_name, match.seeker2.elo
        black_id, black_name, black_elo = match.seeker1.agent_id, match.seeker1.agent_name, match.seeker1.elo
    
    # Create game
    game = ChessGame(
        game_id=game_id,
        white_agent_id=white_id,
        black_agent_id=black_id,
        category=match.category
    )
    
    active_games[game_id] = game
    
    # Update connection state
    manager.set_agent_game(white_id, game_id)
    manager.set_agent_game(black_id, game_id)
    
    # Save to database
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO games (id, white_agent_id, black_agent_id, category, status,
                              elo_white_before, elo_black_before, started_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?, ?)
            """,
            (game_id, white_id, black_id, match.category, white_elo, black_elo,
             datetime.utcnow().isoformat())
        )
        await db.commit()
    
    # Start the game
    game.start()
    
    # Get time control info
    tc = game.clock
    time_control = {
        "base": tc.white_time,
        "increment": tc.increment
    }
    
    # Send game_start to both players
    await manager.send_to_agent(white_id, {
        "event": "game_start",
        "game_id": game_id,
        "color": "white",
        "opponent": {"id": black_id, "name": black_name, "elo": black_elo},
        "fen": game.get_fen(),
        "time_control": time_control
    })
    
    await manager.send_to_agent(black_id, {
        "event": "game_start",
        "game_id": game_id,
        "color": "black",
        "opponent": {"id": white_id, "name": white_name, "elo": white_elo},
        "fen": game.get_fen(),
        "time_control": time_control
    })
    
    print(f"Game {game_id} started: {white_name} vs {black_name} ({match.category})")


async def end_game(game: ChessGame):
    """End a game and update ratings."""
    game_id = game.game_id
    
    # Get Elos before
    async with get_db() as db:
        cursor = await db.execute(
            f"SELECT elo_{game.category} as elo FROM agents WHERE id = ?",
            (game.white_agent_id,)
        )
        white_row = await cursor.fetchone()
        white_elo = white_row["elo"] if white_row else 1200
        
        cursor = await db.execute(
            f"SELECT elo_{game.category} as elo FROM agents WHERE id = ?",
            (game.black_agent_id,)
        )
        black_row = await cursor.fetchone()
        black_elo = black_row["elo"] if black_row else 1200
    
    # Calculate Elo changes
    is_draw = game.result == GameResult.DRAW
    if is_draw:
        white_change, black_change = calculate_elo_change(white_elo, black_elo, is_draw=True)
    elif game.result == GameResult.WHITE_WIN:
        white_change, black_change = calculate_elo_change(white_elo, black_elo)
        black_change = -abs(black_change)  # Ensure loser loses points
    else:  # BLACK_WIN
        black_change, white_change = calculate_elo_change(black_elo, white_elo)
        white_change = -abs(white_change)  # Ensure loser loses points
    
    new_white_elo = apply_elo_floor(white_elo + white_change)
    new_black_elo = apply_elo_floor(black_elo + black_change)
    
    # Determine winner/loser for rate limiting
    white_is_winner = game.result == GameResult.WHITE_WIN
    black_is_winner = game.result == GameResult.BLACK_WIN
    
    # Apply rate limits
    white_cooldown = rate_limiter.apply_game_result(
        game.white_agent_id, game.category, white_is_winner, is_draw
    )
    black_cooldown = rate_limiter.apply_game_result(
        game.black_agent_id, game.category, black_is_winner, is_draw
    )
    
    # Update database
    async with get_db() as db:
        # Update game
        await db.execute(
            """
            UPDATE games SET
                status = 'ended',
                result = ?,
                termination = ?,
                pgn = ?,
                elo_white_after = ?,
                elo_black_after = ?,
                ended_at = ?
            WHERE id = ?
            """,
            (
                game.result.value if game.result else None,
                game.termination.value if game.termination else None,
                game.get_pgn(),
                new_white_elo,
                new_black_elo,
                datetime.utcnow().isoformat(),
                game_id
            )
        )
        
        # Update white agent
        elo_col = f"elo_{game.category}"
        loss_streak_col = f"loss_streak_{game.category}"
        white_loss_streak = 0 if white_is_winner or is_draw else rate_limiter.get_loss_streak(game.white_agent_id, game.category)
        
        await db.execute(
            f"""
            UPDATE agents SET
                {elo_col} = ?,
                games_played = games_played + 1,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                {loss_streak_col} = ?,
                last_game_ended_at = ?
            WHERE id = ?
            """,
            (
                new_white_elo,
                1 if white_is_winner else 0,
                1 if black_is_winner else 0,
                1 if is_draw else 0,
                white_loss_streak,
                datetime.utcnow().isoformat(),
                game.white_agent_id
            )
        )
        
        # Update black agent
        black_loss_streak = 0 if black_is_winner or is_draw else rate_limiter.get_loss_streak(game.black_agent_id, game.category)
        
        await db.execute(
            f"""
            UPDATE agents SET
                {elo_col} = ?,
                games_played = games_played + 1,
                wins = wins + ?,
                losses = losses + ?,
                draws = draws + ?,
                {loss_streak_col} = ?,
                last_game_ended_at = ?
            WHERE id = ?
            """,
            (
                new_black_elo,
                1 if black_is_winner else 0,
                1 if white_is_winner else 0,
                1 if is_draw else 0,
                black_loss_streak,
                datetime.utcnow().isoformat(),
                game.black_agent_id
            )
        )
        
        await db.commit()
    
    # Send game_end to both players
    result_str = game.result.value if game.result else "unknown"
    termination_str = game.termination.value if game.termination else "unknown"
    
    await manager.send_to_agent(game.white_agent_id, {
        "event": "game_end",
        "result": result_str,
        "termination": termination_str,
        "elo_change": white_change,
        "new_elo": new_white_elo,
        "cooldown_seconds": white_cooldown
    })
    
    await manager.send_to_agent(game.black_agent_id, {
        "event": "game_end",
        "result": result_str,
        "termination": termination_str,
        "elo_change": black_change,
        "new_elo": new_black_elo,
        "cooldown_seconds": black_cooldown
    })
    
    # Broadcast to spectators
    await manager.broadcast_to_spectators(game_id, {
        "event": "game_end",
        "result": result_str,
        "termination": termination_str,
        "white_elo_change": white_change,
        "black_elo_change": black_change
    })
    
    # Clean up
    manager.set_agent_game(game.white_agent_id, None)
    manager.set_agent_game(game.black_agent_id, None)
    del active_games[game_id]
    
    print(f"Game {game_id} ended: {result_str} by {termination_str}")


async def handle_agent_disconnect(agent_id: str):
    """Handle an agent disconnecting."""
    game_id = manager.get_agent_game(agent_id)
    
    if game_id and game_id in active_games:
        game = active_games[game_id]
        
        # Record disconnect time
        if agent_id == game.white_agent_id:
            game.white_disconnect_time = time.time()
            game.white_connected = False
        else:
            game.black_disconnect_time = time.time()
            game.black_connected = False
        
        # Notify opponent
        opponent_id = game.black_agent_id if agent_id == game.white_agent_id else game.white_agent_id
        await manager.send_to_agent(opponent_id, {
            "event": "opponent_disconnected"
        })
    
    # Remove from matchmaking queues
    await matchmaking.remove_all_seeks(agent_id)


async def handle_agent_reconnect(agent_id: str):
    """Handle an agent reconnecting."""
    game_id = manager.get_agent_game(agent_id)
    
    if game_id and game_id in active_games:
        game = active_games[game_id]
        
        # Clear disconnect time
        if agent_id == game.white_agent_id:
            game.white_disconnect_time = None
            game.white_connected = True
        else:
            game.black_disconnect_time = None
            game.black_connected = True
        
        # Send current state
        state = game.get_state_dict()
        state["event"] = "state"
        state["reconnected"] = True
        await manager.send_to_agent(agent_id, state)
        
        # Notify opponent
        opponent_id = game.black_agent_id if agent_id == game.white_agent_id else game.white_agent_id
        await manager.send_to_agent(opponent_id, {
            "event": "opponent_reconnected"
        })


async def disconnect_monitor():
    """Monitor disconnected players and forfeit after timeout."""
    DISCONNECT_TIMEOUT = 120  # 2 minutes
    
    while True:
        try:
            now = time.time()
            games_to_end = []
            
            for game_id, game in active_games.items():
                if game.status != GameStatus.ACTIVE:
                    continue
                
                # Check white disconnect
                if game.white_disconnect_time:
                    if now - game.white_disconnect_time >= DISCONNECT_TIMEOUT:
                        games_to_end.append((game, True))  # True = white disconnected
                        continue
                
                # Check black disconnect
                if game.black_disconnect_time:
                    if now - game.black_disconnect_time >= DISCONNECT_TIMEOUT:
                        games_to_end.append((game, False))  # False = black disconnected
                        continue
                
                # Also check for timeout (clock ran out)
                timed_out = game.clock.is_timeout()
                if timed_out is not None:
                    game._end_by_timeout(timed_out)
                    games_to_end.append((game, None))  # None = timeout, not disconnect
            
            for game, white_disconnected in games_to_end:
                if white_disconnected is not None:
                    import chess
                    color = chess.WHITE if white_disconnected else chess.BLACK
                    game.end_by_disconnect(color)
                await end_game(game)
            
            await asyncio.sleep(1)  # Check every second
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Disconnect monitor error: {e}")
            await asyncio.sleep(1)


async def on_match_found(match: MatchResult):
    """Callback when matchmaking finds a match."""
    await create_game(match)


async def on_search_widened(seeker: Seeker, elo_range: list):
    """Callback when search range widens."""
    await manager.send_to_agent(seeker.agent_id, {
        "event": "search_widened",
        "category": seeker.category,
        "elo_range": elo_range
    })


def setup_matchmaking():
    """Set up matchmaking callbacks."""
    matchmaking.on_match = on_match_found
    matchmaking.on_widening = on_search_widened


async def start_background_tasks():
    """Start background tasks."""
    global disconnect_monitor_task
    
    setup_matchmaking()
    await matchmaking.start()
    disconnect_monitor_task = asyncio.create_task(disconnect_monitor())


async def stop_background_tasks():
    """Stop background tasks."""
    global disconnect_monitor_task
    
    await matchmaking.stop()
    if disconnect_monitor_task:
        disconnect_monitor_task.cancel()
        try:
            await disconnect_monitor_task
        except asyncio.CancelledError:
            pass
