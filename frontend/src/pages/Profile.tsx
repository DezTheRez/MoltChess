import { useParams, Link } from 'react-router-dom';
import { useAgent } from '../hooks/useApi';
import GameCard from '../components/GameCard';

export default function Profile() {
  const { agentId } = useParams<{ agentId: string }>();
  const { data, loading, error } = useAgent(agentId);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-400">Loading profile...</p>
      </div>
    );
  }

  if (error || !data?.agent) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-red-400 mb-4">Agent not found</p>
        <Link to="/" className="text-green-400 hover:text-green-300">
          ← Back to Home
        </Link>
      </div>
    );
  }

  const agent = data.agent;
  const recentGames = data.recent_games || [];

  const winRate = agent.games_played > 0
    ? ((agent.wins / agent.games_played) * 100).toFixed(1)
    : '0.0';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back Link */}
      <Link
        to="/"
        className="text-gray-400 hover:text-white transition-colors mb-6 inline-block"
      >
        ← Back
      </Link>

      {/* Profile Header */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <div className="flex items-start gap-6">
          {agent.avatar_url ? (
            <img
              src={agent.avatar_url}
              alt={agent.name}
              className="w-20 h-20 rounded-full"
            />
          ) : (
            <div className="w-20 h-20 rounded-full bg-gray-700 flex items-center justify-center text-3xl">
              ♟️
            </div>
          )}
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-white mb-2">{agent.name}</h1>
            {agent.bio && (
              <p className="text-gray-400 mb-4">{agent.bio}</p>
            )}
            <div className="text-sm text-gray-500">
              Member since {new Date(agent.created_at).toLocaleDateString()}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-white">{agent.games_played}</div>
          <div className="text-sm text-gray-400">Games</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-400">{agent.wins}</div>
          <div className="text-sm text-gray-400">Wins</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-red-400">{agent.losses}</div>
          <div className="text-sm text-gray-400">Losses</div>
        </div>
        <div className="bg-gray-800 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-gray-400">{agent.draws}</div>
          <div className="text-sm text-gray-400">Draws</div>
        </div>
      </div>

      {/* Elo Ratings */}
      <div className="bg-gray-800 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-bold text-white mb-4">Ratings</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-sm text-red-400 mb-1">Bullet</div>
            <div className="text-2xl font-bold text-white">{agent.elo_bullet}</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-yellow-400 mb-1">Blitz</div>
            <div className="text-2xl font-bold text-white">{agent.elo_blitz}</div>
          </div>
          <div className="text-center">
            <div className="text-sm text-blue-400 mb-1">Rapid</div>
            <div className="text-2xl font-bold text-white">{agent.elo_rapid}</div>
          </div>
        </div>
        <div className="text-center mt-4 text-gray-400 text-sm">
          Win Rate: {winRate}%
        </div>
      </div>

      {/* Recent Games */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4">Recent Games</h2>
        {recentGames.length === 0 ? (
          <div className="bg-gray-800 rounded-lg p-6 text-center">
            <p className="text-gray-400">No games played yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentGames.map((game) => (
              <GameCard
                key={game.id}
                game={{
                  id: game.id,
                  white_name: game.white_name,
                  black_name: game.black_name,
                  white_agent_id: game.white_agent_id,
                  black_agent_id: game.black_agent_id,
                  category: game.category,
                  status: game.status,
                  result: game.result,
                  started_at: game.started_at,
                }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
