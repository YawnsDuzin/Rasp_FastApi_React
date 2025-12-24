/**
 * Toggle Switch Component
 */

import clsx from 'clsx';

interface ToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  disabled?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export default function Toggle({
  checked,
  onChange,
  label,
  disabled = false,
  size = 'md',
}: ToggleProps) {
  const sizes = {
    sm: { track: 'h-5 w-9', handle: 'h-3 w-3', translate: 'translate-x-5' },
    md: { track: 'h-6 w-11', handle: 'h-4 w-4', translate: 'translate-x-6' },
    lg: { track: 'h-7 w-14', handle: 'h-5 w-5', translate: 'translate-x-8' },
  };

  return (
    <label className="flex items-center gap-3 cursor-pointer">
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={clsx(
          'toggle-switch',
          sizes[size].track,
          checked ? 'on bg-primary-500' : 'off bg-gray-300 dark:bg-gray-600',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <span
          className={clsx(
            'toggle-switch-handle',
            sizes[size].handle,
            checked ? sizes[size].translate : 'translate-x-1'
          )}
        />
      </button>
      {label && (
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </span>
      )}
    </label>
  );
}
