/**
 * Gauge Chart Component
 *
 * Circular gauge for displaying values.
 */

import clsx from 'clsx';

interface GaugeChartProps {
  value: number;
  max: number;
  label: string;
  unit: string;
  color?: string;
  size?: 'sm' | 'md' | 'lg';
  showWarning?: boolean;
  warningThreshold?: number;
}

export default function GaugeChart({
  value,
  max,
  label,
  unit,
  color = '#0ea5e9',
  size = 'md',
  showWarning = false,
  warningThreshold = 80,
}: GaugeChartProps) {
  const percentage = Math.min((value / max) * 100, 100);
  const isWarning = showWarning && percentage >= warningThreshold;

  const sizes = {
    sm: { container: 'w-24 h-24', text: 'text-lg', label: 'text-xs' },
    md: { container: 'w-32 h-32', text: 'text-2xl', label: 'text-sm' },
    lg: { container: 'w-40 h-40', text: 'text-3xl', label: 'text-base' },
  };

  const strokeWidth = size === 'sm' ? 6 : size === 'md' ? 8 : 10;
  const radius = 50 - strokeWidth / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  const gaugeColor = isWarning ? '#ef4444' : color;

  return (
    <div className={clsx('relative', sizes[size].container)}>
      <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
        {/* Background circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Value circle */}
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={gaugeColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="gauge-value">
        <span className={clsx('font-bold text-gray-900 dark:text-white', sizes[size].text)}>
          {value.toFixed(1)}
        </span>
        <span className={clsx('text-gray-500 dark:text-gray-400', sizes[size].label)}>
          {unit}
        </span>
        <span className={clsx('text-gray-600 dark:text-gray-300 mt-1', sizes[size].label)}>
          {label}
        </span>
      </div>
    </div>
  );
}
