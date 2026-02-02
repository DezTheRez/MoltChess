import { useState, useEffect, useRef, useCallback } from 'react';
import type { GameState, WSMessage } from '../types';
import { config } from '../config';

interface UseSpectatorOptions {
  gameId: string;
  onGameEnd?: (data: WSMessage) => void;
}

export function useSpectator({ gameId, onGameEnd }: UseSpectatorOptions) {
  const [connected, setConnected] = useState(false);
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const ws = new WebSocket(config.ws.watch(gameId));
    console.log('[WS] Connecting to:', config.ws.watch(gameId));

    ws.onopen = () => {
      console.log('[WS] Connection opened');
      setConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      console.log('[WS] Message received:', event.data);
      try {
        const data: WSMessage = JSON.parse(event.data);
        console.log('[WS] Parsed event:', data.event);

        if (data.event === 'state') {
          setGameState({
            fen: data.fen as string,
            last_move: data.last_move as string | undefined,
            clock_white: data.clock_white as number,
            clock_black: data.clock_black as number,
            to_move: data.to_move as 'white' | 'black',
            move_number: data.move_number as number,
            spectator_count: data.spectator_count as number | undefined,
          });
        } else if (data.event === 'game_end') {
          onGameEnd?.(data);
        } else if (data.event === 'error') {
          setError(data.message as string);
        }
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onclose = (event) => {
      console.log('[WS] Connection closed:', event.code, event.reason);
      setConnected(false);
      // Try to reconnect after 3 seconds
      reconnectTimeoutRef.current = window.setTimeout(() => {
        console.log('[WS] Attempting reconnect...');
        connect();
      }, 3000);
    };

    ws.onerror = (event) => {
      console.log('[WS] Error:', event);
      setError('WebSocket connection error');
    };

    wsRef.current = ws;
  }, [gameId, onGameEnd]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: 'ping' }));
    }
  }, []);

  // Keep connection alive
  useEffect(() => {
    const interval = setInterval(sendPing, 30000);
    return () => clearInterval(interval);
  }, [sendPing]);

  return {
    connected,
    gameState,
    error,
  };
}
