import { Link } from 'react-router-dom';
import type { GameSummary, Category } from '../types';

interface GameCardProps {
  game: GameSummary;
  showCategory?: boolean;
}

const categoryLabels: Record<Category, string> = {
  bullet: 'Bullet',
  blitz: 'Blitz',
  rapid: 'Rapid',
};

const categoryColors: Record<Category, string> = {
  bullet: 'bg-red-500',
  blitz: 'bg-yellow-500',
  rapid: 'bg-blue-500',
};

export default function GameCard({ game, showCategory = true }: GameCardProps) {
  const isLive = game.status === 'active';

  return (
    <Link
      to={isLive ? `/game/${game.id}` : `/replay/${game.id}`}
      className="block bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors border border-gray-700 hover:border-gray-600"
    >
      <div className="flex items-center justify-between mb-3">
        {showCategory && (
          <span className={`${categoryColors[game.category]} text-white text-xs px-2 py-1 rounded font-medium`}>
            {categoryLabels[game.category]}
          </span>
        )}
        {isLive && (
          <span className="flex items-center gap-1 text-green-400 text-sm">
            <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
            LIVE
          </span>
        )}
        {!isLive && game.result && (
          <span className="text-gray-400 text-xs">
            {game.result === 'white_win' ? '1-0' : game.result === 'black_win' ? '0-1' : '½-½'}
          </span>
        )}
      </div>

      <div className="space-y-2">
        {/* White Player */}
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-white rounded-sm border border-gray-600"></div>
          <span className="text-white font-medium flex-1 truncate">{game.white_name}</span>
          {game.white_elo && (
            <span className="text-gray-400 text-sm">{game.white_elo}</span>
          )}
        </div>

        {/* Black Player */}
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gray-900 rounded-sm border border-gray-600"></div>
          <span className="text-white font-medium flex-1 truncate">{game.black_name}</span>
          {game.black_elo && (
            <span className="text-gray-400 text-sm">{game.black_elo}</span>
          )}
        </div>
      </div>
    </Link>
  );
}
