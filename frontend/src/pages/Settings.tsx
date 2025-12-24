/**
 * Settings Page
 *
 * Application configuration and simulation controls.
 */

import { useState } from 'react';
import { useStore } from '../hooks/useStore';
import { hardwareApi, systemApi } from '../services/api';
import Toggle from '../components/Toggle';
import Slider from '../components/Slider';
import {
  Settings as SettingsIcon,
  Cpu,
  Database,
  Sliders,
  Info,
  RefreshCw,
} from 'lucide-react';

export default function Settings() {
  const { config, darkMode, toggleDarkMode } = useStore();
  const [simValues, setSimValues] = useState({
    temperature: 25,
    humidity: 50,
    distance: 100,
    motion: false,
    light: 500,
  });
  const [loading, setLoading] = useState(false);

  const handleSimValueChange = async (key: string, value: number | boolean) => {
    setSimValues((prev) => ({ ...prev, [key]: value }));

    if (!config?.simulation_mode) return;

    try {
      await hardwareApi.setSimulationValues({ [key]: value });
    } catch (error) {
      console.error('Failed to set simulation value:', error);
    }
  };

  const handleSimulateButton = async (index: number) => {
    if (!config?.simulation_mode) return;

    setLoading(true);
    try {
      await hardwareApi.simulateButtonPress(index);
    } catch (error) {
      console.error('Failed to simulate button:', error);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* App Info */}
      <div className="card">
        <h3 className="card-header">
          <Info className="w-5 h-5 text-blue-500" />
          Application Information
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">App Name</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.app_name ?? 'Raspberry Pi HMI'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Version</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.app_version ?? '1.0.0'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Mode</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.simulation_mode ? 'Simulation' : 'Hardware'}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Debug</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.debug ? 'Enabled' : 'Disabled'}
            </p>
          </div>
        </div>
      </div>

      {/* UI Settings */}
      <div className="card">
        <h3 className="card-header">
          <SettingsIcon className="w-5 h-5 text-gray-500" />
          UI Settings
        </h3>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
            <div>
              <p className="font-medium text-gray-900 dark:text-white">Dark Mode</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Toggle dark/light theme
              </p>
            </div>
            <Toggle checked={darkMode} onChange={toggleDarkMode} />
          </div>
        </div>
      </div>

      {/* Hardware Settings */}
      <div className="card">
        <h3 className="card-header">
          <Cpu className="w-5 h-5 text-green-500" />
          Hardware Configuration
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Update Interval
            </span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.hardware_update_interval ?? 0.5}s
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Data Log Interval
            </span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.data_log_interval ?? 5}s
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Data Retention
            </span>
            <p className="font-medium text-gray-900 dark:text-white">
              {config?.data_retention_days ?? 30} days
            </p>
          </div>
        </div>
      </div>

      {/* Simulation Controls */}
      {config?.simulation_mode && (
        <div className="card">
          <h3 className="card-header">
            <Sliders className="w-5 h-5 text-purple-500" />
            Simulation Controls
          </h3>
          <div className="space-y-6">
            {/* Temperature */}
            <div>
              <Slider
                value={simValues.temperature}
                min={-10}
                max={50}
                step={0.5}
                onChange={(value) => setSimValues((prev) => ({ ...prev, temperature: value }))}
                onChangeEnd={(value) => handleSimValueChange('temperature', value)}
                label="Temperature"
                unit="°C"
              />
            </div>

            {/* Humidity */}
            <div>
              <Slider
                value={simValues.humidity}
                min={0}
                max={100}
                step={1}
                onChange={(value) => setSimValues((prev) => ({ ...prev, humidity: value }))}
                onChangeEnd={(value) => handleSimValueChange('humidity', value)}
                label="Humidity"
                unit="%"
              />
            </div>

            {/* Distance */}
            <div>
              <Slider
                value={simValues.distance}
                min={0}
                max={400}
                step={1}
                onChange={(value) => setSimValues((prev) => ({ ...prev, distance: value }))}
                onChangeEnd={(value) => handleSimValueChange('distance', value)}
                label="Distance"
                unit="cm"
              />
            </div>

            {/* Light */}
            <div>
              <Slider
                value={simValues.light}
                min={0}
                max={1023}
                step={1}
                onChange={(value) => setSimValues((prev) => ({ ...prev, light: value }))}
                onChangeEnd={(value) => handleSimValueChange('light', value)}
                label="Light Level"
                unit=""
              />
            </div>

            {/* Motion Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">Motion Detected</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Simulate PIR sensor trigger
                </p>
              </div>
              <Toggle
                checked={simValues.motion}
                onChange={(value) => handleSimValueChange('motion', value)}
              />
            </div>

            {/* Button Simulation */}
            <div>
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Simulate Button Press
              </p>
              <div className="flex gap-2">
                {[0, 1, 2, 3].map((index) => (
                  <button
                    key={index}
                    onClick={() => handleSimulateButton(index)}
                    className="btn-secondary flex-1"
                    disabled={loading}
                  >
                    Button {index + 1}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Management */}
      <div className="card">
        <h3 className="card-header">
          <Database className="w-5 h-5 text-orange-500" />
          Data Management
        </h3>
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Sensor data and logs are stored in SQLite database with WAL mode for optimal
            performance on Raspberry Pi's SD card.
          </p>
          <div className="flex gap-4">
            <button
              onClick={async () => {
                if (confirm('Export all data? This may take a moment.')) {
                  // TODO: Implement data export
                  alert('Data export feature coming soon');
                }
              }}
              className="btn-secondary"
            >
              Export Data
            </button>
            <button
              onClick={async () => {
                if (confirm('Delete data older than 30 days?')) {
                  try {
                    const result = await import('../services/api').then((m) =>
                      m.dataApi.cleanupData(30)
                    );
                    alert(`Deleted ${result.deleted_records} old records`);
                  } catch (error) {
                    console.error('Failed to cleanup:', error);
                  }
                }
              }}
              className="btn-danger"
            >
              Cleanup Old Data
            </button>
          </div>
        </div>
      </div>

      {/* API Documentation Link */}
      <div className="card">
        <h3 className="card-header">
          <RefreshCw className="w-5 h-5 text-cyan-500" />
          API Documentation
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Interactive API documentation is available for developers.
        </p>
        <div className="flex gap-4">
          <a
            href="/api/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
          >
            Swagger UI
          </a>
          <a
            href="/api/redoc"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
          >
            ReDoc
          </a>
        </div>
      </div>
    </div>
  );
}
