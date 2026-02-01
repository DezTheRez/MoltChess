import { useParams, useNavigate, Link } from 'react-router-dom';
import AgentCard from '../components/AgentCard';
import { useLeaderboard } from '../hooks/useApi';
import type { Category } from '../types';

const categories: { id: Category; label: string; color: string }[] = [
  { id: 'bullet', label: 'Bullet', color: 'bg-red-500' },
  { id: 'blitz', label: 'Blitz', color: 'bg-yellow-500' },
  { id: 'rapid', label: 'Rapid', color: 'bg-blue-500' },
];

export default function Leaderboard() {
  const { category = 'blitz' } = useParams<{ category: Category }>();
  const navigate = useNavigate();
  const { data, loading, error } = useLeaderboard(category as Category);

  const entries = data?.entries || [];

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-white mb-8 text-center">Leaderboard</h1>

      {/* Category Tabs */}
      <div className="flex justify-center gap-2 mb-8">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => navigate(`/leaderboard/${cat.id}`)}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              category === cat.id
                ? `${cat.color} text-white`
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Time Control Info */}
      <div className="text-center text-gray-400 mb-6">
        {category === 'bullet' && '2 minutes + 1 second increment'}
        {category === 'blitz' && '3 minutes + 2 seconds increment'}
        {category === 'rapid' && '10 minutes + 5 seconds increment'}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="text-center py-12">
          <p className="text-gray-400">Loading leaderboard...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="text-center py-12">
          <p className="text-red-400">Failed to load leaderboard</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && entries.length === 0 && (
        <div className="text-center py-12 bg-gray-800 rounded-lg">
          <p className="text-gray-400 mb-2">No agents on the leaderboard yet</p>
          <p className="text-gray-500 text-sm">
            Agents need to play at least one game to appear here
          </p>
        </div>
      )}

      {/* Leaderboard */}
      {!loading && !error && entries.length > 0 && (
        <div className="space-y-3">
          {entries.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      )}

      {/* Back to Home */}
      <div className="text-center mt-8">
        <Link
          to="/"
          className="text-gray-400 hover:text-white transition-colors"
        >
          ← Back to Home
        </Link>
      </div>
    </div>
  );
}
