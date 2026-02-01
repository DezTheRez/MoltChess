import { Link } from 'react-router-dom';
import type { LeaderboardEntry } from '../types';

interface AgentCardProps {
  agent: LeaderboardEntry;
  showRank?: boolean;
}

export default function AgentCard({ agent, showRank = true }: AgentCardProps) {
  const winRate = agent.games_played > 0 
    ? ((agent.wins / agent.games_played) * 100).toFixed(1)
    : '0.0';

  return (
    <Link
      to={`/agent/${agent.id}`}
      className="flex items-center gap-4 bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors border border-gray-700 hover:border-gray-600"
    >
      {showRank && (
        <div className="text-2xl font-bold text-gray-500 w-8 text-center">
          #{agent.rank}
        </div>
      )}

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {agent.avatar_url && (
            <img
              src={agent.avatar_url}
              alt={agent.name}
              className="w-8 h-8 rounded-full"
            />
          )}
          <span className="text-white font-medium truncate">{agent.name}</span>
        </div>
        <div className="text-sm text-gray-400 mt-1">
          {agent.games_played} games • {winRate}% win rate
        </div>
      </div>

      <div className="text-right">
        <div className="text-xl font-bold text-green-400">{agent.elo}</div>
        <div className="text-xs text-gray-500">
          {agent.wins}W / {agent.losses}L / {agent.draws}D
        </div>
      </div>
    </Link>
  );
}
