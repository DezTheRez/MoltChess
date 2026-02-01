"""Chess game engine using python-chess."""

import chess
import chess.pgn
import io
import time
from typing import Optional, Literal, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class GameStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"


class GameResult(Enum):
    WHITE_WIN = "white_win"
    BLACK_WIN = "black_win"
    DRAW = "draw"


class Termination(Enum):
    CHECKMATE = "checkmate"
    TIMEOUT = "timeout"
    STALEMATE = "stalemate"
    INSUFFICIENT = "insufficient"
    REPETITION = "repetition"
    FIFTY_MOVE = "fifty_move"
    DISCONNECT = "disconnect"


@dataclass
class TimeControl:
    base_time: float  # seconds
    increment: float  # seconds
    
    @classmethod
    def from_category(cls, category: str) -> "TimeControl":
        controls = {
            "bullet": cls(120, 1),   # 2+1
            "blitz": cls(180, 2),    # 3+2
            "rapid": cls(600, 5),    # 10+5
        }
        return controls.get(category, controls["blitz"])


@dataclass
class Clock:
    white_time: float
    black_time: float
    increment: float
    last_move_time: Optional[float] = None
    active_color: chess.Color = chess.WHITE
    
    def start(self):
        """Start the clock."""
        self.last_move_time = time.time()
    
    def switch(self) -> float:
        """
        Switch active player, add increment to the player who just moved.
        Returns time remaining for the player who just moved.
        """
        now = time.time()
        elapsed = now - self.last_move_time if self.last_move_time else 0
        
        # Deduct time from active player
        if self.active_color == chess.WHITE:
            self.white_time -= elapsed
            self.white_time += self.increment  # Add increment
            remaining = self.white_time
        else:
            self.black_time -= elapsed
            self.black_time += self.increment  # Add increment
            remaining = self.black_time
        
        # Switch active color
        self.active_color = not self.active_color
        self.last_move_time = now
        
        return remaining
    
    def get_current_times(self) -> Tuple[float, float]:
        """Get current times accounting for elapsed time on active clock."""
        if self.last_move_time is None:
            return self.white_time, self.black_time
        
        elapsed = time.time() - self.last_move_time
        
        if self.active_color == chess.WHITE:
            return max(0, self.white_time - elapsed), self.black_time
        else:
            return self.white_time, max(0, self.black_time - elapsed)
    
    def is_timeout(self) -> Optional[chess.Color]:
        """Check if either player has timed out. Returns the color that timed out, or None."""
        white, black = self.get_current_times()
        if white <= 0:
            return chess.WHITE
        if black <= 0:
            return chess.BLACK
        return None


@dataclass
class ChessGame:
    """Represents an active chess game."""
    
    game_id: str
    white_agent_id: str
    black_agent_id: str
    category: str
    
    board: chess.Board = field(default_factory=chess.Board)
    clock: Optional[Clock] = None
    status: GameStatus = GameStatus.PENDING
    result: Optional[GameResult] = None
    termination: Optional[Termination] = None
    
    moves: list[str] = field(default_factory=list)  # UCI moves
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    white_connected: bool = False
    black_connected: bool = False
    white_disconnect_time: Optional[float] = None
    black_disconnect_time: Optional[float] = None
    
    spectator_count: int = 0
    
    def __post_init__(self):
        tc = TimeControl.from_category(self.category)
        self.clock = Clock(tc.base_time, tc.base_time, tc.increment)
    
    def start(self):
        """Start the game."""
        self.status = GameStatus.ACTIVE
        self.started_at = datetime.utcnow()
        self.clock.start()
    
    def make_move(self, uci_move: str) -> Tuple[bool, Optional[str]]:
        """
        Attempt to make a move.
        
        Returns:
            Tuple of (success, error_message)
        """
        if self.status != GameStatus.ACTIVE:
            return False, "Game is not active"
        
        # Check timeout first
        timed_out = self.clock.is_timeout()
        if timed_out is not None:
            self._end_by_timeout(timed_out)
            return False, "Time out"
        
        # Parse and validate move
        try:
            move = chess.Move.from_uci(uci_move)
        except ValueError:
            return False, "Invalid move format"
        
        if move not in self.board.legal_moves:
            return False, "Illegal move"
        
        # Make the move
        self.board.push(move)
        self.moves.append(uci_move)
        
        # Switch clock
        self.clock.switch()
        
        # Check for game end conditions
        self._check_game_end()
        
        return True, None
    
    def _check_game_end(self):
        """Check all game end conditions."""
        if self.board.is_checkmate():
            winner = chess.BLACK if self.board.turn == chess.WHITE else chess.WHITE
            self.result = GameResult.WHITE_WIN if winner == chess.WHITE else GameResult.BLACK_WIN
            self.termination = Termination.CHECKMATE
            self._end_game()
        
        elif self.board.is_stalemate():
            self.result = GameResult.DRAW
            self.termination = Termination.STALEMATE
            self._end_game()
        
        elif self.board.is_insufficient_material():
            self.result = GameResult.DRAW
            self.termination = Termination.INSUFFICIENT
            self._end_game()
        
        elif self.board.can_claim_threefold_repetition():
            self.result = GameResult.DRAW
            self.termination = Termination.REPETITION
            self._end_game()
        
        elif self.board.can_claim_fifty_moves():
            self.result = GameResult.DRAW
            self.termination = Termination.FIFTY_MOVE
            self._end_game()
    
    def _end_by_timeout(self, timed_out_color: chess.Color):
        """End game due to timeout."""
        self.result = GameResult.BLACK_WIN if timed_out_color == chess.WHITE else GameResult.WHITE_WIN
        self.termination = Termination.TIMEOUT
        self._end_game()
    
    def end_by_disconnect(self, disconnected_color: chess.Color):
        """End game due to disconnect forfeit."""
        self.result = GameResult.BLACK_WIN if disconnected_color == chess.WHITE else GameResult.WHITE_WIN
        self.termination = Termination.DISCONNECT
        self._end_game()
    
    def _end_game(self):
        """Mark game as ended."""
        self.status = GameStatus.ENDED
        self.ended_at = datetime.utcnow()
    
    def get_fen(self) -> str:
        """Get current board position in FEN."""
        return self.board.fen()
    
    def get_pgn(self) -> str:
        """Generate PGN for the game."""
        game = chess.pgn.Game()
        game.headers["Event"] = "MoltChess Arena"
        game.headers["Site"] = "moltchess.io"
        game.headers["Date"] = self.started_at.strftime("%Y.%m.%d") if self.started_at else "????.??.??"
        game.headers["White"] = self.white_agent_id
        game.headers["Black"] = self.black_agent_id
        game.headers["TimeControl"] = f"{int(TimeControl.from_category(self.category).base_time)}+{int(TimeControl.from_category(self.category).increment)}"
        
        if self.result:
            result_map = {
                GameResult.WHITE_WIN: "1-0",
                GameResult.BLACK_WIN: "0-1",
                GameResult.DRAW: "1/2-1/2",
            }
            game.headers["Result"] = result_map[self.result]
        
        if self.termination:
            game.headers["Termination"] = self.termination.value
        
        # Add moves
        node = game
        temp_board = chess.Board()
        for uci_move in self.moves:
            move = chess.Move.from_uci(uci_move)
            node = node.add_variation(move)
            temp_board.push(move)
        
        return str(game)
    
    def to_move(self) -> Literal["white", "black"]:
        """Get whose turn it is."""
        return "white" if self.board.turn == chess.WHITE else "black"
    
    def get_agent_color(self, agent_id: str) -> Optional[Literal["white", "black"]]:
        """Get the color for a given agent."""
        if agent_id == self.white_agent_id:
            return "white"
        elif agent_id == self.black_agent_id:
            return "black"
        return None
    
    def is_agent_turn(self, agent_id: str) -> bool:
        """Check if it's this agent's turn."""
        color = self.get_agent_color(agent_id)
        if color is None:
            return False
        return self.to_move() == color
    
    def get_state_dict(self) -> dict:
        """Get current game state as a dictionary."""
        white_time, black_time = self.clock.get_current_times()
        return {
            "fen": self.get_fen(),
            "last_move": self.moves[-1] if self.moves else None,
            "clock_white": round(white_time, 1),
            "clock_black": round(black_time, 1),
            "to_move": self.to_move(),
            "move_number": self.board.fullmove_number,
        }
