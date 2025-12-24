/**
 * Sensors Page
 *
 * Detailed sensor readings and ADC values.
 */

import { useStore } from '../hooks/useStore';
import GaugeChart from '../components/GaugeChart';
import {
  Thermometer,
  Droplets,
  Gauge,
  Ruler,
  Eye,
  Sun,
  Droplet,
  Cpu,
} from 'lucide-react';
import clsx from 'clsx';

export default function Sensors() {
  const { hardwareData } = useStore();

  const sensors = hardwareData?.sensors;
  const adc = hardwareData?.adc;

  return (
    <div className="space-y-6">
      {/* Environmental Sensors */}
      <div className="card">
        <h3 className="card-header">
          <Thermometer className="w-5 h-5 text-orange-500" />
          Environmental Sensors
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {/* Temperature */}
          <div className="flex flex-col items-center p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg">
            <Thermometer className="w-8 h-8 text-orange-500 mb-2" />
            <span className="text-3xl font-bold text-gray-900 dark:text-white">
              {sensors?.temperature?.toFixed(1) ?? '--'}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">°C</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Temperature
            </span>
          </div>

          {/* Humidity */}
          <div className="flex flex-col items-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <Droplets className="w-8 h-8 text-blue-500 mb-2" />
            <span className="text-3xl font-bold text-gray-900 dark:text-white">
              {sensors?.humidity?.toFixed(1) ?? '--'}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">%</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Humidity
            </span>
          </div>

          {/* Pressure */}
          <div className="flex flex-col items-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <Gauge className="w-8 h-8 text-purple-500 mb-2" />
            <span className="text-3xl font-bold text-gray-900 dark:text-white">
              {sensors?.pressure?.toFixed(0) ?? '--'}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">hPa</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Pressure
            </span>
          </div>

          {/* Altitude */}
          <div className="flex flex-col items-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <Gauge className="w-8 h-8 text-green-500 mb-2" />
            <span className="text-3xl font-bold text-gray-900 dark:text-white">
              {sensors?.altitude?.toFixed(1) ?? '--'}
            </span>
            <span className="text-sm text-gray-500 dark:text-gray-400">m</span>
            <span className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Altitude
            </span>
          </div>
        </div>
      </div>

      {/* Other Sensors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Distance */}
        <div className="card">
          <h3 className="card-header">
            <Ruler className="w-5 h-5 text-cyan-500" />
            Distance (Ultrasonic)
          </h3>
          <div className="flex justify-center py-4">
            <GaugeChart
              value={sensors?.distance ?? 0}
              max={400}
              label="Distance"
              unit="cm"
              color="#06b6d4"
            />
          </div>
          <div className="text-center text-sm text-gray-500 dark:text-gray-400">
            HC-SR04 Sensor
          </div>
        </div>

        {/* Motion */}
        <div className="card">
          <h3 className="card-header">
            <Eye className="w-5 h-5 text-red-500" />
            Motion (PIR)
          </h3>
          <div className="flex flex-col items-center py-4">
            <div
              className={clsx(
                'w-24 h-24 rounded-full flex items-center justify-center transition-all duration-500',
                sensors?.motion
                  ? 'bg-red-500 animate-pulse-ring'
                  : 'bg-gray-200 dark:bg-gray-700'
              )}
            >
              <Eye
                className={clsx(
                  'w-12 h-12',
                  sensors?.motion ? 'text-white' : 'text-gray-400'
                )}
              />
            </div>
            <span
              className={clsx(
                'mt-4 text-lg font-bold',
                sensors?.motion
                  ? 'text-red-500'
                  : 'text-gray-500 dark:text-gray-400'
              )}
            >
              {sensors?.motion ? 'Motion Detected!' : 'No Motion'}
            </span>
          </div>
        </div>

        {/* Light */}
        <div className="card">
          <h3 className="card-header">
            <Sun className="w-5 h-5 text-yellow-500" />
            Light Level (LDR)
          </h3>
          <div className="flex justify-center py-4">
            <GaugeChart
              value={sensors?.light_level ?? 0}
              max={1023}
              label="Light"
              unit=""
              color="#eab308"
            />
          </div>
          <div className="flex justify-between px-4 text-xs text-gray-500 dark:text-gray-400">
            <span>Dark</span>
            <span>Bright</span>
          </div>
        </div>
      </div>

      {/* Soil Moisture */}
      <div className="card">
        <h3 className="card-header">
          <Droplet className="w-5 h-5 text-blue-500" />
          Soil Moisture
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="flex justify-center">
            <GaugeChart
              value={sensors?.soil_moisture ?? 0}
              max={1023}
              label="Moisture"
              unit=""
              color="#3b82f6"
              size="lg"
            />
          </div>
          <div className="flex flex-col justify-center space-y-4">
            <div className="flex items-center gap-4">
              <div className="w-4 h-4 rounded bg-red-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                0-300: Dry - Needs water
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-4 h-4 rounded bg-yellow-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                300-600: Moderate
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-4 h-4 rounded bg-green-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                600-900: Good moisture
              </span>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-4 h-4 rounded bg-blue-500" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                900+: Very wet
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ADC Readings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* I2C ADC (ADS1115) */}
        <div className="card">
          <h3 className="card-header">
            <Cpu className="w-5 h-5 text-indigo-500" />
            I2C ADC (ADS1115)
          </h3>
          <div className="space-y-4">
            {adc?.i2c &&
              Object.entries(adc.i2c).map(([channel, voltage]) => (
                <div key={channel} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      Channel {channel}
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {(voltage as number).toFixed(3)} V
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-indigo-500 transition-all duration-300"
                      style={{
                        width: `${((voltage as number) / 3.3) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            {(!adc?.i2c || Object.keys(adc.i2c).length === 0) && (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                No I2C ADC data available
              </p>
            )}
          </div>
        </div>

        {/* SPI ADC (MCP3008) */}
        <div className="card">
          <h3 className="card-header">
            <Cpu className="w-5 h-5 text-pink-500" />
            SPI ADC (MCP3008)
          </h3>
          <div className="space-y-4">
            {adc?.spi &&
              Object.entries(adc.spi).map(([channel, voltage]) => (
                <div key={channel} className="space-y-1">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600 dark:text-gray-400">
                      Channel {channel}
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {(voltage as number).toFixed(3)} V
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-pink-500 transition-all duration-300"
                      style={{
                        width: `${((voltage as number) / 3.3) * 100}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            {(!adc?.spi || Object.keys(adc.spi).length === 0) && (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                No SPI ADC data available
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
