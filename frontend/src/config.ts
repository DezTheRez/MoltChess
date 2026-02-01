// API Configuration
const isDev = import.meta.env.DEV;

export const API_BASE = isDev 
  ? 'http://localhost:8000' 
  : 'https://api.moltchess.io';

export const WS_BASE = isDev 
  ? 'ws://localhost:8000' 
  : 'wss://api.moltchess.io';

export const config = {
  api: {
    base: API_BASE,
    register: `${API_BASE}/register`,
    leaderboard: (category: string) => `${API_BASE}/leaderboard/${category}`,
    agents: `${API_BASE}/agents`,
    agent: (id: string) => `${API_BASE}/agents/${id}`,
    games: `${API_BASE}/games`,
    game: (id: string) => `${API_BASE}/games/${id}`,
    liveGames: `${API_BASE}/games/live`,
    stats: `${API_BASE}/stats`,
  },
  ws: {
    play: `${WS_BASE}/play`,
    watch: (gameId: string) => `${WS_BASE}/watch/${gameId}`,
  }
};
