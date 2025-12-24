/**
 * Dashboard Page
 *
 * Main overview page with key metrics.
 */

import { useStore } from '../hooks/useStore';
import GaugeChart from '../components/GaugeChart';
import {
  Thermometer,
  Droplets,
  Gauge,
  Activity,
  Cpu,
  HardDrive,
  MemoryStick,
  Lightbulb,
  Power,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export default function Dashboard() {
  const { hardwareData, systemMetrics, temperatureHistory, humidityHistory, config } =
    useStore();

  const sensors = hardwareData?.sensors;
  const gpio = hardwareData?.gpio;

  return (
    <div className="space-y-6">
      {/* Simulation Banner */}
      {config?.simulation_mode && (
        <div className="bg-yellow-100 dark:bg-yellow-900/30 border border-yellow-300 dark:border-yellow-700 rounded-lg p-4">
          <p className="text-yellow-800 dark:text-yellow-200 text-sm">
            <strong>Simulation Mode:</strong> Running without hardware. Sensor values are simulated.
          </p>
        </div>
      )}

      {/* Sensor Gauges */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {/* Temperature */}
        <div className="card flex flex-col items-center">
          <div className="flex items-center gap-2 text-orange-500 mb-4">
            <Thermometer className="w-5 h-5" />
            <span className="font-medium">Temperature</span>
          </div>
          <GaugeChart
            value={sensors?.temperature ?? 0}
            max={50}
            label=""
            unit="°C"
            color="#f97316"
            showWarning
            warningThreshold={70}
          />
        </div>

        {/* Humidity */}
        <div className="card flex flex-col items-center">
          <div className="flex items-center gap-2 text-blue-500 mb-4">
            <Droplets className="w-5 h-5" />
            <span className="font-medium">Humidity</span>
          </div>
          <GaugeChart
            value={sensors?.humidity ?? 0}
            max={100}
            label=""
            unit="%"
            color="#3b82f6"
          />
        </div>

        {/* Pressure */}
        <div className="card flex flex-col items-center">
          <div className="flex items-center gap-2 text-purple-500 mb-4">
            <Gauge className="w-5 h-5" />
            <span className="font-medium">Pressure</span>
          </div>
          <GaugeChart
            value={sensors?.pressure ?? 1013}
            max={1100}
            label=""
            unit="hPa"
            color="#a855f7"
          />
        </div>

        {/* Distance */}
        <div className="card flex flex-col items-center">
          <div className="flex items-center gap-2 text-green-500 mb-4">
            <Activity className="w-5 h-5" />
            <span className="font-medium">Distance</span>
          </div>
          <GaugeChart
            value={sensors?.distance ?? 0}
            max={400}
            label=""
            unit="cm"
            color="#22c55e"
          />
        </div>
      </div>

      {/* System Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {/* CPU */}
        <div className="card">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Cpu className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-500 dark:text-gray-400">CPU</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {systemMetrics?.cpu.percent.toFixed(1) ?? 0}%
                </p>
              </div>
            </div>
            {systemMetrics?.cpu.temperature && (
              <div className="text-right">
                <p className="text-xs text-gray-500 dark:text-gray-400">Temp</p>
                <p className="text-lg font-semibold text-orange-500">
                  {systemMetrics.cpu.temperature.toFixed(1)}°C
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Memory */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
              <MemoryStick className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Memory</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemMetrics?.memory.percent.toFixed(1) ?? 0}%
              </p>
            </div>
          </div>
          <div className="mt-3">
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all duration-500"
                style={{ width: `${systemMetrics?.memory.percent ?? 0}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {systemMetrics?.memory.used_gb.toFixed(1)} / {systemMetrics?.memory.total_gb.toFixed(1)} GB
            </p>
          </div>
        </div>

        {/* Disk */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
              <HardDrive className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Disk</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemMetrics?.disk.percent.toFixed(1) ?? 0}%
              </p>
            </div>
          </div>
          <div className="mt-3">
            <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all duration-500"
                style={{ width: `${systemMetrics?.disk.percent ?? 0}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {systemMetrics?.disk.free_gb.toFixed(1)} GB free
            </p>
          </div>
        </div>

        {/* Uptime */}
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
              <Power className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Uptime</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {systemMetrics?.system.uptime_hours.toFixed(1) ?? 0}h
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* GPIO Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LEDs */}
        <div className="card">
          <h3 className="card-header">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            LED Status
          </h3>
          <div className="flex gap-4">
            {gpio &&
              Object.entries(gpio.leds).map(([index, state]) => (
                <div
                  key={index}
                  className="flex flex-col items-center gap-2"
                >
                  <div
                    className={`w-8 h-8 rounded-full transition-all duration-300 ${
                      state
                        ? 'bg-yellow-400 shadow-lg shadow-yellow-400/50'
                        : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  />
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    LED {parseInt(index) + 1}
                  </span>
                </div>
              ))}
          </div>
        </div>

        {/* Relays */}
        <div className="card">
          <h3 className="card-header">
            <Power className="w-5 h-5 text-green-500" />
            Relay Status
          </h3>
          <div className="flex gap-4">
            {gpio &&
              Object.entries(gpio.relays).map(([index, state]) => (
                <div
                  key={index}
                  className="flex flex-col items-center gap-2"
                >
                  <div
                    className={`w-10 h-10 rounded-lg flex items-center justify-center transition-all duration-300 ${
                      state
                        ? 'bg-green-500 text-white'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-400'
                    }`}
                  >
                    <Power className="w-5 h-5" />
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Relay {parseInt(index) + 1}
                  </span>
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Temperature Chart */}
        <div className="card">
          <h3 className="card-header">
            <Thermometer className="w-5 h-5 text-orange-500" />
            Temperature Trend
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={temperatureHistory}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={['auto', 'auto']}
                  tick={{ fontSize: 10 }}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: 'none',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                  name="Temperature"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Humidity Chart */}
        <div className="card">
          <h3 className="card-header">
            <Droplets className="w-5 h-5 text-blue-500" />
            Humidity Trend
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={humidityHistory}>
                <CartesianGrid strokeDasharray="3 3" className="opacity-30" />
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 10 }}
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    border: 'none',
                    borderRadius: '8px',
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="value"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot={false}
                  name="Humidity"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
