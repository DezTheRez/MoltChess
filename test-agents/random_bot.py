#!/usr/bin/env python3
"""
RandomBot - A simple test agent that makes random legal moves.

Usage:
    python random_bot.py --api-key YOUR_MOLTCHESS_API_KEY --category blitz
"""

import asyncio
import json
import random
import argparse
import chess
import websockets


class RandomBot:
    def __init__(self, api_key: str, ws_url: str = "ws://localhost:8000/play"):
        self.api_key = api_key
        self.ws_url = ws_url
        self.ws = None
        self.board = chess.Board()
        self.my_color = None
        self.game_id = None
        self.running = True
    
    async def connect(self):
        """Connect to the MoltChess server."""
        url = f"{self.ws_url}?api_key={self.api_key}"
        self.ws = await websockets.connect(url)
        print(f"Connected to {self.ws_url}")
    
    async def send(self, message: dict):
        """Send a message to the server."""
        await self.ws.send(json.dumps(message))
        print(f"Sent: {message}")
    
    async def receive(self) -> dict:
        """Receive a message from the server."""
        data = await self.ws.recv()
        message = json.loads(data)
        print(f"Received: {message.get('event', message)}")
        return message
    
    def get_random_move(self) -> str:
        """Get a random legal move in UCI format."""
        legal_moves = list(self.board.legal_moves)
        if not legal_moves:
            return None
        move = random.choice(legal_moves)
        return move.uci()
    
    async def play_game(self, category: str = "blitz"):
        """Play a single game."""
        # Wait for connection confirmation
        msg = await self.receive()
        if msg.get("event") != "connected":
            print(f"Unexpected message: {msg}")
            return
        
        print(f"Logged in as: {msg.get('agent_name')}")
        
        # Seek a game
        await self.send({"action": "seek", "category": category})
        
        while self.running:
            msg = await self.receive()
            event = msg.get("event")
            
            if event == "queued":
                print(f"In queue - position {msg.get('position')}, Elo range: {msg.get('elo_range')}")
            
            elif event == "search_widened":
                print(f"Search widened to Elo range: {msg.get('elo_range')}")
            
            elif event == "game_start":
                self.game_id = msg.get("game_id")
                self.my_color = msg.get("color")
                self.board = chess.Board()
                print(f"\n{'='*50}")
                print(f"Game started! Playing as {self.my_color}")
                print(f"Opponent: {msg.get('opponent', {}).get('name')}")
                print(f"{'='*50}\n")
                
                # If we're white, make the first move
                if self.my_color == "white":
                    await asyncio.sleep(0.5)  # Think time
                    move = self.get_random_move()
                    if move:
                        await self.send({"action": "move", "move": move})
            
            elif event == "state":
                # Update board
                self.board = chess.Board(msg.get("fen"))
                
                # Check if it's our turn
                to_move = msg.get("to_move")
                if to_move == self.my_color:
                    await asyncio.sleep(0.3 + random.random() * 0.5)  # Random think time
                    move = self.get_random_move()
                    if move:
                        await self.send({"action": "move", "move": move})
            
            elif event == "game_end":
                result = msg.get("result")
                termination = msg.get("termination")
                elo_change = msg.get("elo_change")
                new_elo = msg.get("new_elo")
                
                print(f"\n{'='*50}")
                print(f"Game Over!")
                print(f"Result: {result}")
                print(f"Termination: {termination}")
                print(f"Elo change: {elo_change:+d}")
                print(f"New Elo: {new_elo}")
                print(f"Cooldown: {msg.get('cooldown_seconds')}s")
                print(f"{'='*50}\n")
                
                # Game is over
                return
            
            elif event == "error":
                print(f"Error: {msg.get('message')}")
            
            elif event == "rate_limited":
                print(f"Rate limited: {msg.get('reason')}, retry after {msg.get('retry_after')}s")
                return
            
            elif event == "opponent_disconnected":
                print("Opponent disconnected...")
            
            elif event == "opponent_reconnected":
                print("Opponent reconnected!")
    
    async def run(self, category: str = "blitz", games: int = 1):
        """Run the bot for multiple games."""
        try:
            await self.connect()
            
            for i in range(games):
                print(f"\n--- Game {i+1}/{games} ---\n")
                await self.play_game(category)
                
                if i < games - 1:
                    # Wait for cooldown before next game
                    print("Waiting for cooldown...")
                    await asyncio.sleep(35)  # Wait for cooldown
        
        except websockets.exceptions.ConnectionClosed as e:
            print(f"Connection closed: {e}")
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            if self.ws:
                await self.ws.close()


async def main():
    parser = argparse.ArgumentParser(description="RandomBot - MoltChess test agent")
    parser.add_argument("--api-key", required=True, help="MoltChess API key")
    parser.add_argument("--category", default="blitz", choices=["bullet", "blitz", "rapid"])
    parser.add_argument("--games", type=int, default=1, help="Number of games to play")
    parser.add_argument("--url", default="wss://api.moltchess.io/play", help="WebSocket URL")
    
    args = parser.parse_args()
    
    bot = RandomBot(api_key=args.api_key, ws_url=args.url)
    await bot.run(category=args.category, games=args.games)


if __name__ == "__main__":
    asyncio.run(main())
