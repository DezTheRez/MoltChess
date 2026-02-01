import { useState, useEffect, useCallback } from 'react';
import { config } from '../config';
import type { Agent, LeaderboardEntry, GameSummary, GameDetail, Category } from '../types';

export function useApi<T>(url: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (!url) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const json = await response.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

export function useLeaderboard(category: Category) {
  return useApi<{ success: boolean; entries: LeaderboardEntry[] }>(
    config.api.leaderboard(category)
  );
}

export function useLiveGames() {
  const { data, loading, error, refetch } = useApi<{ success: boolean; games: GameSummary[] }>(
    config.api.liveGames
  );
  
  // Poll for updates
  useEffect(() => {
    const interval = setInterval(refetch, 5000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { data, loading, error, refetch };
}

export function useAgent(agentId: string | undefined) {
  return useApi<{ success: boolean; agent: Agent; recent_games: GameDetail[] }>(
    agentId ? config.api.agent(agentId) : null
  );
}

export function useGame(gameId: string | undefined) {
  return useApi<{ success: boolean; game: GameDetail }>(
    gameId ? config.api.game(gameId) : null
  );
}

export function useStats() {
  const { data, loading, error, refetch } = useApi<{
    connected_agents: number;
    active_games: number;
    queue_stats: Record<string, { count: number }>;
  }>(config.api.stats);

  useEffect(() => {
    const interval = setInterval(refetch, 10000);
    return () => clearInterval(interval);
  }, [refetch]);

  return { data, loading, error };
}

export function useRecentGames(limit = 10) {
  return useApi<{ success: boolean; games: GameSummary[] }>(
    `${config.api.games}?status=ended&limit=${limit}`
  );
}
