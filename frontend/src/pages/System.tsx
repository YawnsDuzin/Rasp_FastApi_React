/**
 * System Monitoring Page
 *
 * Detailed system metrics and health status.
 */

import { useStore } from '../hooks/useStore';
import GaugeChart from '../components/GaugeChart';
import {
  Cpu,
  MemoryStick,
  HardDrive,
  Thermometer,
  Activity,
  Clock,
  Wifi,
  Server,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { useState, useEffect } from 'react';

export default function System() {
  const { systemMetrics, config } = useStore();
  const [cpuHistory, setCpuHistory] = useState<Array<{ time: string; value: number }>>([]);

  // Track CPU history
  useEffect(() => {
    if (systemMetrics?.cpu.percent !== undefined) {
      const now = new Date();
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      setCpuHistory((prev) => {
        const newHistory = [...prev, { time, value: systemMetrics.cpu.percent }];
        if (newHistory.length > 60) newHistory.shift();
        return newHistory;
      });
    }
  }, [systemMetrics?.cpu.percent]);

  const cpu = systemMetrics?.cpu;
  const memory = systemMetrics?.memory;
  const disk = systemMetrics?.disk;
  const network = systemMetrics?.network;
  const system = systemMetrics?.system;

  return (
    <div className="space-y-6">
      {/* CPU & Temperature */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* CPU Usage */}
        <div className="card">
          <h3 className="card-header">
            <Cpu className="w-5 h-5 text-blue-500" />
            CPU Usage
          </h3>
          <div className="flex items-center justify-center gap-8">
            <GaugeChart
              value={cpu?.percent ?? 0}
              max={100}
              label="Usage"
              unit="%"
              color="#3b82f6"
              size="lg"
              showWarning
              warningThreshold={90}
            />
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Cores</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {cpu?.count ?? 0}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Frequency</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {cpu?.frequency.current.toFixed(0) ?? 0} MHz
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* CPU Temperature */}
        <div className="card">
          <h3 className="card-header">
            <Thermometer className="w-5 h-5 text-orange-500" />
            CPU Temperature
          </h3>
          <div className="flex items-center justify-center gap-8">
            <GaugeChart
              value={cpu?.temperature ?? 0}
              max={85}
              label="Temperature"
              unit="°C"
              color="#f97316"
              size="lg"
              showWarning
              warningThreshold={80}
            />
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-green-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">&lt;60°C Normal</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-yellow-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">60-70°C Warm</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-orange-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">70-80°C Hot</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-red-500" />
                <span className="text-sm text-gray-600 dark:text-gray-400">&gt;80°C Critical</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CPU History Chart */}
      <div className="card">
        <h3 className="card-header">
          <Activity className="w-5 h-5 text-blue-500" />
          CPU Usage History
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={cpuHistory}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={40} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  border: 'none',
                  borderRadius: '8px',
                }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, 'CPU']}
              />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Memory & Disk */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Memory */}
        <div className="card">
          <h3 className="card-header">
            <MemoryStick className="w-5 h-5 text-green-500" />
            Memory Usage
          </h3>
          <div className="flex items-center justify-center gap-8">
            <GaugeChart
              value={memory?.percent ?? 0}
              max={100}
              label="Usage"
              unit="%"
              color="#22c55e"
              size="lg"
              showWarning
              warningThreshold={90}
            />
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Used</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {memory?.used_gb.toFixed(2) ?? 0} GB
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Total</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {memory?.total_gb.toFixed(2) ?? 0} GB
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Disk */}
        <div className="card">
          <h3 className="card-header">
            <HardDrive className="w-5 h-5 text-purple-500" />
            Disk Usage
          </h3>
          <div className="flex items-center justify-center gap-8">
            <GaugeChart
              value={disk?.percent ?? 0}
              max={100}
              label="Usage"
              unit="%"
              color="#a855f7"
              size="lg"
              showWarning
              warningThreshold={90}
            />
            <div className="space-y-3">
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Free</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {disk?.free_gb.toFixed(2) ?? 0} GB
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-500 dark:text-gray-400">Total</span>
                <p className="text-xl font-bold text-gray-900 dark:text-white">
                  {disk?.total_gb.toFixed(2) ?? 0} GB
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Network & Uptime */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Network */}
        <div className="card">
          <h3 className="card-header">
            <Wifi className="w-5 h-5 text-cyan-500" />
            Network I/O
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">Sent</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {network?.sent_mb.toFixed(1) ?? 0}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">MB</p>
            </div>
            <div className="p-4 bg-cyan-50 dark:bg-cyan-900/20 rounded-lg text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">Received</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {network?.recv_mb.toFixed(1) ?? 0}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">MB</p>
            </div>
          </div>
        </div>

        {/* Uptime */}
        <div className="card">
          <h3 className="card-header">
            <Clock className="w-5 h-5 text-amber-500" />
            System Uptime
          </h3>
          <div className="flex items-center justify-center py-4">
            <div className="text-center">
              <p className="text-4xl font-bold text-gray-900 dark:text-white">
                {system?.uptime_hours.toFixed(1) ?? 0}
              </p>
              <p className="text-lg text-gray-500 dark:text-gray-400">hours</p>
              {system?.boot_time && (
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                  Since {new Date(system.boot_time).toLocaleString()}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Platform Info */}
      <div className="card">
        <h3 className="card-header">
          <Server className="w-5 h-5 text-gray-500" />
          Platform Information
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Platform</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.platform.system ?? 'Unknown'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Architecture</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.platform.machine ?? 'Unknown'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Raspberry Pi</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.platform.is_raspberry_pi ? 'Yes' : 'No'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Mode</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.simulation_mode ? 'Simulation' : 'Hardware'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
