import { useEffect, useState } from 'react';

interface ClockProps {
  initialTime: number; // in seconds
  isActive: boolean;
  isRunning: boolean;
  color: 'white' | 'black';
}

export default function Clock({ initialTime, isActive, isRunning, color }: ClockProps) {
  const [time, setTime] = useState(initialTime);

  // Update time when prop changes
  useEffect(() => {
    setTime(initialTime);
  }, [initialTime]);

  // Countdown when active and running
  useEffect(() => {
    if (!isActive || !isRunning) return;

    const interval = setInterval(() => {
      setTime((prev) => Math.max(0, prev - 0.1));
    }, 100);

    return () => clearInterval(interval);
  }, [isActive, isRunning]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const tenths = Math.floor((seconds % 1) * 10);

    if (seconds < 10) {
      return `${mins}:${secs.toString().padStart(2, '0')}.${tenths}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isLow = time < 30;
  const isCritical = time < 10;

  return (
    <div
      className={`
        px-4 py-3 rounded-lg font-mono text-2xl font-bold
        transition-colors duration-200
        ${color === 'white' ? 'bg-white text-gray-900' : 'bg-gray-800 text-white'}
        ${isActive ? 'ring-2 ring-green-400' : ''}
        ${isCritical && isActive ? 'ring-red-500 animate-pulse' : ''}
        ${isLow && isActive ? 'text-red-500' : ''}
      `}
    >
      {formatTime(time)}
    </div>
  );
}
