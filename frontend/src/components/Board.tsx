import { Chessboard } from 'react-chessboard';

interface BoardProps {
  fen: string;
  lastMove?: string;
  orientation?: 'white' | 'black';
  width?: number;
}

export default function Board({ fen, lastMove, orientation = 'white', width = 400 }: BoardProps) {
  // Convert UCI move to squares for highlighting
  const customSquareStyles: Record<string, React.CSSProperties> = {};
  
  if (lastMove && lastMove.length >= 4) {
    const from = lastMove.slice(0, 2);
    const to = lastMove.slice(2, 4);
    
    customSquareStyles[from] = {
      backgroundColor: 'rgba(255, 255, 0, 0.4)',
    };
    customSquareStyles[to] = {
      backgroundColor: 'rgba(255, 255, 0, 0.4)',
    };
  }

  return (
    <div className="rounded-lg overflow-hidden shadow-xl">
      <Chessboard
        position={fen}
        boardWidth={width}
        boardOrientation={orientation}
        customSquareStyles={customSquareStyles}
        arePiecesDraggable={false}
        customDarkSquareStyle={{ backgroundColor: '#769656' }}
        customLightSquareStyle={{ backgroundColor: '#eeeed2' }}
      />
    </div>
  );
}
