import { useParams, Link } from 'react-router-dom';
import { useState, useMemo } from 'react';
import { Chess } from 'chess.js';
import Board from '../components/Board';
import { useGame } from '../hooks/useApi';

export default function Replay() {
  const { gameId } = useParams<{ gameId: string }>();
  const { data, loading, error } = useGame(gameId);
  const [moveIndex, setMoveIndex] = useState(0);

  // Parse PGN and get positions
  const { positions, moves } = useMemo(() => {
    if (!data?.game?.pgn) {
      return { positions: ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'], moves: [] };
    }

    try {
      const chess = new Chess();
      const positions: string[] = [chess.fen()];
      const moves: string[] = [];

      // Load PGN
      chess.loadPgn(data.game.pgn);
      const history = chess.history({ verbose: true });

      // Reset and replay
      chess.reset();
      for (const move of history) {
        chess.move(move);
        positions.push(chess.fen());
        moves.push(move.from + move.to + (move.promotion || ''));
      }

      return { positions, moves };
    } catch (e) {
      console.error('Failed to parse PGN:', e);
      return { positions: ['rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'], moves: [] };
    }
  }, [data?.game?.pgn]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-gray-400">Loading game...</p>
      </div>
    );
  }

  if (error || !data?.game) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8 text-center">
        <p className="text-red-400 mb-4">Game not found</p>
        <Link to="/" className="text-green-400 hover:text-green-300">
          ← Back to Home
        </Link>
      </div>
    );
  }

  const game = data.game;
  const currentFen = positions[moveIndex];
  const lastMove = moveIndex > 0 ? moves[moveIndex - 1] : undefined;

  const goToStart = () => setMoveIndex(0);
  const goBack = () => setMoveIndex(Math.max(0, moveIndex - 1));
  const goForward = () => setMoveIndex(Math.min(positions.length - 1, moveIndex + 1));
  const goToEnd = () => setMoveIndex(positions.length - 1);

  const resultText = {
    white_win: '1-0',
    black_win: '0-1',
    draw: '½-½',
  }[game.result || ''] || '*';

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Back Link */}
      <Link
        to="/"
        className="text-gray-400 hover:text-white transition-colors mb-6 inline-block"
      >
        ← Back
      </Link>

      {/* Game Header */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-white font-medium">{game.white_name}</span>
              <span className="text-gray-500">vs</span>
              <span className="text-white font-medium">{game.black_name}</span>
            </div>
            <div className="text-sm text-gray-400">
              {game.category.charAt(0).toUpperCase() + game.category.slice(1)} •{' '}
              {game.termination && game.termination.charAt(0).toUpperCase() + game.termination.slice(1)}
            </div>
          </div>
          <div className="text-2xl font-bold text-white">{resultText}</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[1fr,250px] gap-6">
        {/* Board */}
        <div className="flex flex-col items-center">
          {/* Black Player */}
          <div className="w-full max-w-[400px] flex items-center gap-3 mb-3">
            <div className="w-4 h-4 bg-gray-900 rounded-sm border border-gray-600"></div>
            <span className="text-white">{game.black_name}</span>
            {game.elo_black_before && (
              <span className="text-gray-500 text-sm">({game.elo_black_before})</span>
            )}
          </div>

          <Board fen={currentFen} lastMove={lastMove} width={400} />

          {/* White Player */}
          <div className="w-full max-w-[400px] flex items-center gap-3 mt-3">
            <div className="w-4 h-4 bg-white rounded-sm border border-gray-600"></div>
            <span className="text-white">{game.white_name}</span>
            {game.elo_white_before && (
              <span className="text-gray-500 text-sm">({game.elo_white_before})</span>
            )}
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center gap-2 mt-6">
            <button
              onClick={goToStart}
              disabled={moveIndex === 0}
              className="p-2 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ⏮️
            </button>
            <button
              onClick={goBack}
              disabled={moveIndex === 0}
              className="p-2 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ◀️
            </button>
            <span className="px-4 text-gray-400 text-sm">
              Move {moveIndex} / {positions.length - 1}
            </span>
            <button
              onClick={goForward}
              disabled={moveIndex === positions.length - 1}
              className="p-2 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ▶️
            </button>
            <button
              onClick={goToEnd}
              disabled={moveIndex === positions.length - 1}
              className="p-2 bg-gray-800 rounded hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ⏭️
            </button>
          </div>
        </div>

        {/* Move List */}
        <div className="bg-gray-800 rounded-lg p-4 max-h-[500px] overflow-y-auto">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Moves</h3>
          <div className="space-y-1 font-mono text-sm">
            {moves.length === 0 ? (
              <p className="text-gray-500">No moves</p>
            ) : (
              moves.map((move, i) => (
                <button
                  key={i}
                  onClick={() => setMoveIndex(i + 1)}
                  className={`block w-full text-left px-2 py-1 rounded ${
                    moveIndex === i + 1
                      ? 'bg-green-600 text-white'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  {Math.floor(i / 2) + 1}.{i % 2 === 0 ? '' : '..'} {move}
                </button>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Elo Changes */}
      {game.elo_white_after && game.elo_black_after && (
        <div className="mt-6 bg-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-medium text-gray-400 mb-3">Rating Changes</h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="text-center">
              <div className="text-white">{game.white_name}</div>
              <div className="text-sm">
                <span className="text-gray-400">{game.elo_white_before}</span>
                <span className="text-gray-500"> → </span>
                <span className="text-white">{game.elo_white_after}</span>
                <span className={`ml-2 ${
                  game.elo_white_after > (game.elo_white_before || 0)
                    ? 'text-green-400'
                    : game.elo_white_after < (game.elo_white_before || 0)
                    ? 'text-red-400'
                    : 'text-gray-400'
                }`}>
                  ({game.elo_white_after - (game.elo_white_before || 0) >= 0 ? '+' : ''}
                  {game.elo_white_after - (game.elo_white_before || 0)})
                </span>
              </div>
            </div>
            <div className="text-center">
              <div className="text-white">{game.black_name}</div>
              <div className="text-sm">
                <span className="text-gray-400">{game.elo_black_before}</span>
                <span className="text-gray-500"> → </span>
                <span className="text-white">{game.elo_black_after}</span>
                <span className={`ml-2 ${
                  game.elo_black_after > (game.elo_black_before || 0)
                    ? 'text-green-400'
                    : game.elo_black_after < (game.elo_black_before || 0)
                    ? 'text-red-400'
                    : 'text-gray-400'
                }`}>
                  ({game.elo_black_after - (game.elo_black_before || 0) >= 0 ? '+' : ''}
                  {game.elo_black_after - (game.elo_black_before || 0)})
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
