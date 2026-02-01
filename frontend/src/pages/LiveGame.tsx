import { useParams, useNavigate } from 'react-router-dom';
import { useState, useCallback } from 'react';
import Board from '../components/Board';
import Clock from '../components/Clock';
import { useSpectator } from '../hooks/useWebSocket';
import { useGame } from '../hooks/useApi';
import type { WSMessage } from '../types';

export default function LiveGame() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const [gameEnded, setGameEnded] = useState(false);
  const [endResult, setEndResult] = useState<WSMessage | null>(null);

  const { data: gameData } = useGame(gameId);

  const handleGameEnd = useCallback((data: WSMessage) => {
    setGameEnded(true);
    setEndResult(data);
  }, []);

  const { connected, gameState, error } = useSpectator({
    gameId: gameId || '',
    onGameEnd: handleGameEnd,
  });

  if (!gameId) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <p className="text-red-400">Invalid game ID</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-8 text-center">
        <p className="text-red-400 mb-4">{error}</p>
        <button
          onClick={() => navigate('/')}
          className="text-green-400 hover:text-green-300"
        >
          ← Back to Home
        </button>
      </div>
    );
  }

  const game = gameData?.game;
  const whiteName = game?.white_name || 'White';
  const blackName = game?.black_name || 'Black';
  const category = game?.category || 'blitz';

  const categoryLabels = {
    bullet: 'Bullet (2+1)',
    blitz: 'Blitz (3+2)',
    rapid: 'Rapid (10+5)',
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-white transition-colors"
        >
          ← Back
        </button>
        <div className="flex items-center gap-4">
          <span className="text-gray-400">{categoryLabels[category as keyof typeof categoryLabels]}</span>
          {connected && !gameEnded && (
            <span className="flex items-center gap-1 text-green-400 text-sm">
              <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
              LIVE
            </span>
          )}
          {gameEnded && (
            <span className="text-yellow-400 text-sm font-medium">ENDED</span>
          )}
        </div>
      </div>

      {/* Game Ended Overlay */}
      {gameEnded && endResult && (
        <div className="bg-gray-800 rounded-lg p-6 mb-6 text-center border border-gray-700">
          <h2 className="text-2xl font-bold text-white mb-2">Game Over</h2>
          <p className="text-xl text-gray-300">
            {endResult.result === 'white_win' && `${whiteName} wins!`}
            {endResult.result === 'black_win' && `${blackName} wins!`}
            {endResult.result === 'draw' && "It's a draw!"}
          </p>
          <p className="text-gray-400 mt-2">
            by {endResult.termination}
          </p>
          <button
            onClick={() => navigate(`/replay/${gameId}`)}
            className="mt-4 bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg transition-colors"
          >
            View Replay
          </button>
        </div>
      )}

      <div className="grid lg:grid-cols-[1fr,300px] gap-8">
        {/* Board Section */}
        <div className="flex flex-col items-center">
          {/* Black Player Info */}
          <div className="w-full max-w-[400px] flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-gray-900 rounded-sm border border-gray-600"></div>
              <span className="text-white font-medium">{blackName}</span>
            </div>
            {gameState && (
              <Clock
                initialTime={gameState.clock_black}
                isActive={gameState.to_move === 'black'}
                isRunning={connected && !gameEnded}
                color="black"
              />
            )}
          </div>

          {/* Chess Board */}
          {gameState ? (
            <Board
              fen={gameState.fen}
              lastMove={gameState.last_move}
              width={400}
            />
          ) : (
            <div className="w-[400px] h-[400px] bg-gray-800 rounded-lg flex items-center justify-center">
              <p className="text-gray-400">
                {connected ? 'Loading game...' : 'Connecting...'}
              </p>
            </div>
          )}

          {/* White Player Info */}
          <div className="w-full max-w-[400px] flex items-center justify-between mt-4">
            <div className="flex items-center gap-3">
              <div className="w-4 h-4 bg-white rounded-sm border border-gray-600"></div>
              <span className="text-white font-medium">{whiteName}</span>
            </div>
            {gameState && (
              <Clock
                initialTime={gameState.clock_white}
                isActive={gameState.to_move === 'white'}
                isRunning={connected && !gameEnded}
                color="white"
              />
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Game Info */}
          <div className="bg-gray-800 rounded-lg p-4">
            <h3 className="text-sm font-medium text-gray-400 mb-3">Game Info</h3>
            {gameState && (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">Move</span>
                  <span className="text-white">{gameState.move_number}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">To Move</span>
                  <span className="text-white capitalize">{gameState.to_move}</span>
                </div>
                {gameState.spectator_count !== undefined && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Spectators</span>
                    <span className="text-white">{gameState.spectator_count}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Connection Status */}
          <div className="bg-gray-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  connected ? 'bg-green-400' : 'bg-red-400'
                }`}
              ></div>
              <span className="text-sm text-gray-400">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
