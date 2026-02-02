interface EvalBarProps {
  evaluation: number | null;
  mateIn: number | null;
  height?: number;
}

export default function EvalBar({ evaluation, mateIn, height = 400 }: EvalBarProps) {
  // Calculate white's percentage (50% = equal)
  let whitePercent = 50;
  let displayText = '0.0';

  if (mateIn !== null) {
    // Mate detected: positive = white mates, negative = black mates
    whitePercent = mateIn > 0 ? 100 : 0;
    displayText = `M${Math.abs(mateIn)}`;
  } else if (evaluation !== null) {
    // Clamp evaluation to [-5, 5] for display, map to [0, 100]
    const clamped = Math.max(-5, Math.min(5, evaluation));
    whitePercent = 50 + (clamped / 5) * 50;
    displayText = evaluation > 0 ? `+${evaluation.toFixed(1)}` : evaluation.toFixed(1);
  }

  const blackPercent = 100 - whitePercent;

  return (
    <div className="flex flex-col items-center">
      <div 
        className="w-[30px] rounded overflow-hidden border border-gray-600 relative flex flex-col"
        style={{ height }}
      >
        {/* Black side (top) */}
        <div 
          className="bg-gray-700 transition-all duration-300 ease-out"
          style={{ height: `${blackPercent}%` }}
        />
        {/* White side (bottom) */}
        <div 
          className="bg-white transition-all duration-300 ease-out flex-1"
        />
      </div>
      <span className="text-xs text-gray-400 mt-1 font-mono">{displayText}</span>
    </div>
  );
}
