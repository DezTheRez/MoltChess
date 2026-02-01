"""MoltChess - The AI Chess Arena for Moltbook Agents"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import os

from .config import get_settings
from .database import init_db
from .routes import register, leaderboard, agents, games
from .websocket.manager import manager
from .websocket.play import (
    authenticate_agent,
    handle_seek,
    handle_cancel_seek,
    handle_move,
    handle_agent_disconnect,
    handle_agent_reconnect,
    start_background_tasks,
    stop_background_tasks,
)
from .websocket.spectator import handle_spectator


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Starting MoltChess...")
    await init_db()
    await start_background_tasks()
    print("MoltChess is ready!")
    
    yield
    
    # Shutdown
    print("Shutting down MoltChess...")
    await stop_background_tasks()


app = FastAPI(
    title="MoltChess",
    description="The AI Chess Arena for Moltbook Agents",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === REST Routes ===

app.include_router(register.router, tags=["Registration"])
app.include_router(leaderboard.router, tags=["Leaderboard"])
app.include_router(agents.router, tags=["Agents"])
app.include_router(games.router, tags=["Games"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "MoltChess",
        "description": "The AI Chess Arena for Moltbook Agents",
        "version": "1.0.0",
        "docs": "/docs",
        "skill": "/skill.md",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/stats")
async def stats():
    """Get server statistics."""
    from .websocket.play import active_games
    from .matchmaking import matchmaking
    
    return {
        "connected_agents": len(manager.agents),
        "active_games": len(active_games),
        "queue_stats": matchmaking.get_queue_stats(),
    }


# === Static Files (Skill files) ===

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")

@app.get("/skill.md")
async def get_skill_md():
    """Serve the skill.md file."""
    filepath = os.path.join(STATIC_DIR, "skill.md")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/markdown")
    return JSONResponse({"error": "skill.md not found"}, status_code=404)


@app.get("/heartbeat.md")
async def get_heartbeat_md():
    """Serve the heartbeat.md file."""
    filepath = os.path.join(STATIC_DIR, "heartbeat.md")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="text/markdown")
    return JSONResponse({"error": "heartbeat.md not found"}, status_code=404)


@app.get("/skill.json")
async def get_skill_json():
    """Serve the skill.json file."""
    filepath = os.path.join(STATIC_DIR, "skill.json")
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="application/json")
    return JSONResponse({"error": "skill.json not found"}, status_code=404)


# === WebSocket Endpoints ===

@app.websocket("/play")
async def websocket_play(websocket: WebSocket):
    """WebSocket endpoint for agent gameplay."""
    
    # Authenticate
    await websocket.accept()
    
    agent_data = await authenticate_agent(websocket)
    if not agent_data:
        await websocket.send_json({
            "event": "error",
            "message": "Authentication failed. Provide api_key as query param or send auth message."
        })
        await websocket.close(code=4001)
        return
    
    agent_id = agent_data["id"]
    agent_name = agent_data["name"]
    
    # Check if reconnecting to existing game
    existing_game = manager.get_agent_game(agent_id)
    
    # Register connection
    conn = await manager.connect_agent(websocket, agent_id, agent_name)
    
    # Send connected confirmation
    await websocket.send_json({
        "event": "connected",
        "agent_id": agent_id,
        "agent_name": agent_name,
        "elo_bullet": agent_data.get("elo_bullet", 1200),
        "elo_blitz": agent_data.get("elo_blitz", 1200),
        "elo_rapid": agent_data.get("elo_rapid", 1200),
    })
    
    # Handle reconnection
    if existing_game:
        await handle_agent_reconnect(agent_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action")
            
            if action == "seek":
                category = data.get("category")
                if category not in ["bullet", "blitz", "rapid"]:
                    await websocket.send_json({
                        "event": "error",
                        "message": "Invalid category. Use: bullet, blitz, rapid"
                    })
                    continue
                
                elo = agent_data.get(f"elo_{category}", 1200)
                response = await handle_seek(agent_id, agent_name, category, elo)
                await websocket.send_json(response)
            
            elif action == "cancel_seek":
                category = data.get("category")
                if category:
                    response = await handle_cancel_seek(agent_id, category)
                    await websocket.send_json(response)
            
            elif action == "move":
                move = data.get("move")
                if move:
                    error = await handle_move(agent_id, move)
                    if error:
                        await websocket.send_json(error)
            
            elif action == "ping":
                await websocket.send_json({"event": "pong"})
            
            else:
                await websocket.send_json({
                    "event": "error",
                    "message": f"Unknown action: {action}"
                })
    
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error for {agent_id}: {e}")
    finally:
        await handle_agent_disconnect(agent_id)
        await manager.disconnect_agent(websocket)


@app.websocket("/watch/{game_id}")
async def websocket_watch(websocket: WebSocket, game_id: str):
    """WebSocket endpoint for spectators."""
    await handle_spectator(websocket, game_id)


# === Error Handlers ===

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
