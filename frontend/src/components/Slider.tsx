/**
 * Slider Component
 */

import { useState, useEffect } from 'react';
import clsx from 'clsx';

interface SliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
  onChangeEnd?: (value: number) => void;
  label?: string;
  unit?: string;
  disabled?: boolean;
  showValue?: boolean;
}

export default function Slider({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  onChangeEnd,
  label,
  unit = '',
  disabled = false,
  showValue = true,
}: SliderProps) {
  const [localValue, setLocalValue] = useState(value);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    if (!isDragging) {
      setLocalValue(value);
    }
  }, [value, isDragging]);

  const percentage = ((localValue - min) / (max - min)) * 100;

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value);
    setLocalValue(newValue);
    onChange(newValue);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    if (onChangeEnd) {
      onChangeEnd(localValue);
    }
  };

  return (
    <div className="w-full">
      {(label || showValue) && (
        <div className="flex justify-between mb-2">
          {label && (
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-sm font-medium text-primary-600 dark:text-primary-400">
              {localValue.toFixed(step < 1 ? 1 : 0)}
              {unit}
            </span>
          )}
        </div>
      )}
      <div className="relative">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={localValue}
          onChange={handleChange}
          onMouseDown={() => setIsDragging(true)}
          onMouseUp={handleMouseUp}
          onTouchStart={() => setIsDragging(true)}
          onTouchEnd={handleMouseUp}
          disabled={disabled}
          className={clsx(
            'w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer',
            'focus:outline-none focus:ring-2 focus:ring-primary-500',
            disabled && 'opacity-50 cursor-not-allowed'
          )}
          style={{
            background: `linear-gradient(to right, #0ea5e9 0%, #0ea5e9 ${percentage}%, #e5e7eb ${percentage}%, #e5e7eb 100%)`,
          }}
        />
      </div>
      <div className="flex justify-between mt-1">
        <span className="text-xs text-gray-500 dark:text-gray-400">{min}</span>
        <span className="text-xs text-gray-500 dark:text-gray-400">{max}</span>
      </div>
    </div>
  );
}
