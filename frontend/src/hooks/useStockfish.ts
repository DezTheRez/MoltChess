import { useState, useEffect, useRef, useCallback } from 'react';

interface StockfishResult {
  evaluation: number | null;
  mateIn: number | null;
  isReady: boolean;
  evaluate: (fen: string) => void;
}

export function useStockfish(depth: number = 10): StockfishResult {
  const [evaluation, setEvaluation] = useState<number | null>(null);
  const [mateIn, setMateIn] = useState<number | null>(null);
  const [isReady, setIsReady] = useState(false);
  const engineRef = useRef<Worker | null>(null);
  const currentFenRef = useRef<string>('');

  useEffect(() => {
    // Initialize Stockfish Web Worker
    const worker = new Worker('/stockfish.js');
    engineRef.current = worker;

    worker.onmessage = (event) => {
      const line = event.data;
      
      if (line === 'uciok') {
        worker.postMessage('isready');
      } else if (line === 'readyok') {
        setIsReady(true);
      } else if (typeof line === 'string' && line.includes('depth') && line.includes('score')) {
        // Only process lines with depth info (final or intermediate results)
        const depthMatch = line.match(/depth (\d+)/);
        const currentDepth = depthMatch ? parseInt(depthMatch[1], 10) : 0;
        
        // Only update on our target depth or higher
        if (currentDepth >= depth) {
          if (line.includes('score cp')) {
            // Parse centipawn score
            const match = line.match(/score cp (-?\d+)/);
            if (match) {
              const cp = parseInt(match[1], 10);
              // Flip evaluation if it's black's turn (FEN contains ' b ')
              const isBlackTurn = currentFenRef.current.includes(' b ');
              const adjustedCp = isBlackTurn ? -cp : cp;
              setEvaluation(adjustedCp / 100); // Convert to pawns
              setMateIn(null);
            }
          } else if (line.includes('score mate')) {
            // Parse mate score
            const match = line.match(/score mate (-?\d+)/);
            if (match) {
              const mateValue = parseInt(match[1], 10);
              // Flip for black's turn
              const isBlackTurn = currentFenRef.current.includes(' b ');
              setMateIn(isBlackTurn ? -mateValue : mateValue);
              setEvaluation(null);
            }
          }
        }
      }
    };

    worker.onerror = (error) => {
      console.error('Stockfish worker error:', error);
    };

    worker.postMessage('uci');

    return () => {
      worker.terminate();
    };
  }, [depth]);

  const evaluate = useCallback((fen: string) => {
    if (engineRef.current && isReady) {
      currentFenRef.current = fen;
      engineRef.current.postMessage('stop');
      engineRef.current.postMessage(`position fen ${fen}`);
      engineRef.current.postMessage(`go depth ${depth}`);
    }
  }, [isReady, depth]);

  return { evaluation, mateIn, isReady, evaluate };
}
