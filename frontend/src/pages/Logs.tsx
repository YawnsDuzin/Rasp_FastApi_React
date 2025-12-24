/**
 * Logs Page
 *
 * System logs and event history.
 */

import { useState, useEffect } from 'react';
import { dataApi } from '../services/api';
import {
  FileText,
  AlertCircle,
  AlertTriangle,
  Info,
  Bug,
  RefreshCw,
  Trash2,
} from 'lucide-react';
import clsx from 'clsx';

interface LogEntry {
  id: number;
  timestamp: string;
  level: string;
  source: string;
  message: string;
  details: Record<string, unknown> | null;
  user_action: boolean;
}

const LOG_LEVELS = ['ALL', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'];

export default function Logs() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLevel, setSelectedLevel] = useState('ALL');
  const [hours, setHours] = useState(24);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const level = selectedLevel === 'ALL' ? undefined : selectedLevel;
      const data = await dataApi.getSystemLogs(level, hours, 200);
      setLogs(data as LogEntry[]);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchLogs();
    // Refresh every 30 seconds
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, [selectedLevel, hours]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return <AlertCircle className="w-4 h-4" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4" />;
      case 'INFO':
        return <Info className="w-4 h-4" />;
      case 'DEBUG':
        return <Bug className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/30';
      case 'ERROR':
        return 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-900/20';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-900/20';
      case 'INFO':
        return 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-900/20';
      case 'DEBUG':
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-800';
      default:
        return 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-800';
    }
  };

  const handleCleanup = async () => {
    if (confirm('Are you sure you want to delete old logs?')) {
      try {
        const result = await dataApi.cleanupData(30);
        alert(`Deleted ${result.deleted_records} old records`);
        fetchLogs();
      } catch (error) {
        console.error('Failed to cleanup:', error);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          {/* Level Filter */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Level:</span>
            <div className="flex gap-1">
              {LOG_LEVELS.map((level) => (
                <button
                  key={level}
                  onClick={() => setSelectedLevel(level)}
                  className={clsx(
                    'px-3 py-1 text-sm rounded-lg transition-colors',
                    selectedLevel === level
                      ? 'bg-primary-500 text-white'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                  )}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Time Range */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-500 dark:text-gray-400">Period:</span>
            <select
              value={hours}
              onChange={(e) => setHours(parseInt(e.target.value))}
              className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 rounded-lg border-none"
            >
              <option value={1}>Last 1 hour</option>
              <option value={6}>Last 6 hours</option>
              <option value={24}>Last 24 hours</option>
              <option value={72}>Last 3 days</option>
              <option value={168}>Last 7 days</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex gap-2 ml-auto">
            <button
              onClick={fetchLogs}
              className="btn-secondary flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw className={clsx('w-4 h-4', loading && 'animate-spin')} />
              Refresh
            </button>
            <button
              onClick={handleCleanup}
              className="btn-danger flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Cleanup
            </button>
          </div>
        </div>
      </div>

      {/* Log Count */}
      <div className="text-sm text-gray-500 dark:text-gray-400">
        Showing {logs.length} log entries
      </div>

      {/* Log List */}
      <div className="card p-0 overflow-hidden">
        {loading && logs.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 animate-spin text-primary-500" />
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <FileText className="w-12 h-12 text-gray-300 dark:text-gray-600 mb-4" />
            <p className="text-gray-500 dark:text-gray-400">No logs found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-700">
            {logs.map((log) => (
              <div
                key={log.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <div className="flex items-start gap-4">
                  {/* Level Badge */}
                  <div
                    className={clsx(
                      'flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium',
                      getLevelColor(log.level)
                    )}
                  >
                    {getLevelIcon(log.level)}
                    {log.level}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {log.source}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                      {log.user_action && (
                        <span className="px-2 py-0.5 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 rounded">
                          User Action
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-300 break-words">
                      {log.message}
                    </p>
                    {log.details && (
                      <pre className="mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs overflow-x-auto">
                        {JSON.stringify(log.details, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
