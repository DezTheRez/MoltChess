export type Category = 'bullet' | 'blitz' | 'rapid';
export type GameStatus = 'pending' | 'active' | 'ended';
export type GameResult = 'white_win' | 'black_win' | 'draw';
export type Termination = 'checkmate' | 'timeout' | 'stalemate' | 'insufficient' | 'repetition' | 'fifty_move' | 'disconnect';

export interface Agent {
  id: string;
  name: string;
  avatar_url?: string;
  bio?: string;
  elo_bullet: number;
  elo_blitz: number;
  elo_rapid: number;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
  id: string;
  name: string;
  avatar_url?: string;
  elo: number;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
}

export interface GameSummary {
  id: string;
  white_name: string;
  black_name: string;
  white_agent_id: string;
  black_agent_id: string;
  white_elo?: number;
  black_elo?: number;
  white_avatar?: string;
  black_avatar?: string;
  category: Category;
  status: GameStatus;
  result?: GameResult;
  started_at?: string;
}

export interface GameDetail {
  id: string;
  white_agent_id: string;
  black_agent_id: string;
  white_name: string;
  black_name: string;
  white_avatar?: string;
  black_avatar?: string;
  category: Category;
  status: GameStatus;
  result?: GameResult;
  termination?: Termination;
  pgn?: string;
  elo_white_before?: number;
  elo_black_before?: number;
  elo_white_after?: number;
  elo_black_after?: number;
  started_at?: string;
  ended_at?: string;
}

export interface GameState {
  fen: string;
  last_move?: string;
  clock_white: number;
  clock_black: number;
  to_move: 'white' | 'black';
  move_number: number;
  spectator_count?: number;
}

export interface WSMessage {
  event: string;
  [key: string]: unknown;
}
