"""WebSocket handler for spectators."""

from fastapi import WebSocket, WebSocketDisconnect

from .manager import manager
from .play import active_games


async def handle_spectator(websocket: WebSocket, game_id: str):
    """Handle a spectator connection."""
    print(f"[SPECTATOR] New spectator attempting to join game {game_id}")
    
    # Check if game exists
    if game_id not in active_games:
        print(f"[SPECTATOR] Game {game_id} not found in active_games")
        await websocket.accept()
        await websocket.send_json({
            "event": "error",
            "message": "Game not found or has ended"
        })
        await websocket.close()
        return
    
    game = active_games[game_id]
    
    # Connect spectator
    await manager.connect_spectator(websocket, game_id)
    
    try:
        # Send current state
        state = game.get_state_dict()
        state["event"] = "state"
        state["game_id"] = game_id
        state["white_agent_id"] = game.white_agent_id
        state["black_agent_id"] = game.black_agent_id
        state["category"] = game.category
        state["spectator_count"] = manager.get_spectator_count(game_id)
        
        await websocket.send_json(state)
        print(f"[SPECTATOR] Sent initial state to spectator for game {game_id}")
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Just keep the connection alive, spectators don't send meaningful messages
                data = await websocket.receive_json()
                print(f"[SPECTATOR] Received from spectator: {data}")
                
                # Handle ping/pong
                if data.get("action") == "ping":
                    await websocket.send_json({"event": "pong"})
                    
            except WebSocketDisconnect:
                print(f"[SPECTATOR] WebSocketDisconnect for game {game_id}")
                break
            except Exception as e:
                print(f"[SPECTATOR] Error in spectator loop: {e}")
                break
                
    finally:
        print(f"[SPECTATOR] Cleaning up spectator for game {game_id}")
        await manager.disconnect_spectator(websocket, game_id)
