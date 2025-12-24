/**
 * Hardware Control Page
 *
 * Control GPIOs, PWM, and NeoPixels.
 */

import { useState } from 'react';
import { useStore } from '../hooks/useStore';
import { hardwareApi } from '../services/api';
import Toggle from '../components/Toggle';
import Slider from '../components/Slider';
import { Lightbulb, Power, Gauge, RotateCw, Palette } from 'lucide-react';
import clsx from 'clsx';

const NEOPIXEL_EFFECTS = [
  { id: 'rainbow', label: 'Rainbow' },
  { id: 'breathing', label: 'Breathing' },
  { id: 'chase', label: 'Chase' },
  { id: 'sparkle', label: 'Sparkle' },
  { id: 'wave', label: 'Wave' },
  { id: 'fire', label: 'Fire' },
];

const NEOPIXEL_COLORS = [
  { name: 'Red', value: '#FF0000' },
  { name: 'Green', value: '#00FF00' },
  { name: 'Blue', value: '#0000FF' },
  { name: 'Yellow', value: '#FFFF00' },
  { name: 'Cyan', value: '#00FFFF' },
  { name: 'Magenta', value: '#FF00FF' },
  { name: 'White', value: '#FFFFFF' },
  { name: 'Orange', value: '#FFA500' },
];

export default function Hardware() {
  const { hardwareData } = useStore();
  const [motorSpeed, setMotorSpeed] = useState(0);
  const [servoAngle, setServoAngle] = useState(90);
  const [loading, setLoading] = useState<string | null>(null);

  const gpio = hardwareData?.gpio;
  const pwm = hardwareData?.pwm;

  // LED Control
  const handleLedToggle = async (index: number, state: boolean) => {
    setLoading(`led-${index}`);
    try {
      await hardwareApi.setLed(index, state);
    } catch (error) {
      console.error('Failed to set LED:', error);
    }
    setLoading(null);
  };

  // Relay Control
  const handleRelayToggle = async (index: number, state: boolean) => {
    setLoading(`relay-${index}`);
    try {
      await hardwareApi.setRelay(index, state);
    } catch (error) {
      console.error('Failed to set relay:', error);
    }
    setLoading(null);
  };

  // Motor Control
  const handleMotorChange = async (speed: number) => {
    setMotorSpeed(speed);
    try {
      await hardwareApi.setMotorSpeed(speed);
    } catch (error) {
      console.error('Failed to set motor speed:', error);
    }
  };

  // Servo Control
  const handleServoChange = async (angle: number) => {
    setServoAngle(angle);
    try {
      await hardwareApi.setServoAngle(angle);
    } catch (error) {
      console.error('Failed to set servo angle:', error);
    }
  };

  // NeoPixel Color
  const handleNeopixelColor = async (color: string) => {
    setLoading('neopixel-color');
    try {
      await hardwareApi.setNeopixelColor(null, color);
    } catch (error) {
      console.error('Failed to set NeoPixel color:', error);
    }
    setLoading(null);
  };

  // NeoPixel Effect
  const handleNeopixelEffect = async (effect: string) => {
    setLoading(`neopixel-${effect}`);
    try {
      await hardwareApi.startNeopixelEffect(effect);
    } catch (error) {
      console.error('Failed to start effect:', error);
    }
    setLoading(null);
  };

  // NeoPixel Clear
  const handleNeopixelClear = async () => {
    setLoading('neopixel-clear');
    try {
      await hardwareApi.clearNeopixel();
    } catch (error) {
      console.error('Failed to clear NeoPixel:', error);
    }
    setLoading(null);
  };

  return (
    <div className="space-y-6">
      {/* GPIO Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LEDs */}
        <div className="card">
          <h3 className="card-header">
            <Lightbulb className="w-5 h-5 text-yellow-500" />
            LED Control
          </h3>
          <div className="space-y-4">
            {gpio &&
              Object.entries(gpio.leds).map(([index, state]) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={clsx(
                        'w-4 h-4 rounded-full transition-all duration-300',
                        state
                          ? 'bg-yellow-400 shadow-md shadow-yellow-400/50'
                          : 'bg-gray-300 dark:bg-gray-600'
                      )}
                    />
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      LED {parseInt(index) + 1}
                    </span>
                  </div>
                  <Toggle
                    checked={state}
                    onChange={(newState) => handleLedToggle(parseInt(index), newState)}
                    disabled={loading === `led-${index}`}
                  />
                </div>
              ))}
            {gpio && Object.keys(gpio.leds).length > 0 && (
              <div className="flex gap-2 mt-4">
                <button
                  onClick={() => hardwareApi.setAllLeds(true)}
                  className="btn-primary flex-1"
                >
                  All On
                </button>
                <button
                  onClick={() => hardwareApi.setAllLeds(false)}
                  className="btn-secondary flex-1"
                >
                  All Off
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Relays */}
        <div className="card">
          <h3 className="card-header">
            <Power className="w-5 h-5 text-green-500" />
            Relay Control
          </h3>
          <div className="space-y-4">
            {gpio &&
              Object.entries(gpio.relays).map(([index, state]) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Power
                      className={clsx(
                        'w-5 h-5 transition-colors',
                        state ? 'text-green-500' : 'text-gray-400'
                      )}
                    />
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      Relay {parseInt(index) + 1}
                    </span>
                  </div>
                  <Toggle
                    checked={state}
                    onChange={(newState) => handleRelayToggle(parseInt(index), newState)}
                    disabled={loading === `relay-${index}`}
                  />
                </div>
              ))}
          </div>
        </div>
      </div>

      {/* PWM Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Motor */}
        <div className="card">
          <h3 className="card-header">
            <Gauge className="w-5 h-5 text-blue-500" />
            Motor Speed Control
          </h3>
          <div className="p-4">
            <Slider
              value={pwm?.motor_speed ?? motorSpeed}
              min={0}
              max={100}
              step={1}
              onChange={setMotorSpeed}
              onChangeEnd={handleMotorChange}
              label="Speed"
              unit="%"
            />
          </div>
        </div>

        {/* Servo */}
        <div className="card">
          <h3 className="card-header">
            <RotateCw className="w-5 h-5 text-purple-500" />
            Servo Angle Control
          </h3>
          <div className="p-4">
            <Slider
              value={pwm?.servo_angle ?? servoAngle}
              min={0}
              max={180}
              step={1}
              onChange={setServoAngle}
              onChangeEnd={handleServoChange}
              label="Angle"
              unit="°"
            />
            <div className="flex justify-between mt-4">
              <button
                onClick={() => handleServoChange(0)}
                className="btn-secondary text-sm"
              >
                0°
              </button>
              <button
                onClick={() => handleServoChange(90)}
                className="btn-secondary text-sm"
              >
                90°
              </button>
              <button
                onClick={() => handleServoChange(180)}
                className="btn-secondary text-sm"
              >
                180°
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* NeoPixel Control */}
      <div className="card">
        <h3 className="card-header">
          <Palette className="w-5 h-5 text-pink-500" />
          NeoPixel LED Strip
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Colors */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Solid Colors
            </h4>
            <div className="grid grid-cols-4 gap-2">
              {NEOPIXEL_COLORS.map((color) => (
                <button
                  key={color.name}
                  onClick={() => handleNeopixelColor(color.value)}
                  className={clsx(
                    'w-full aspect-square rounded-lg transition-transform hover:scale-105',
                    loading === 'neopixel-color' && 'opacity-50'
                  )}
                  style={{ backgroundColor: color.value }}
                  title={color.name}
                />
              ))}
            </div>
          </div>

          {/* Effects */}
          <div>
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
              Effects
            </h4>
            <div className="grid grid-cols-2 gap-2">
              {NEOPIXEL_EFFECTS.map((effect) => (
                <button
                  key={effect.id}
                  onClick={() => handleNeopixelEffect(effect.id)}
                  className={clsx(
                    'btn-secondary text-sm',
                    loading === `neopixel-${effect.id}` && 'opacity-50'
                  )}
                >
                  {effect.label}
                </button>
              ))}
            </div>
            <button
              onClick={handleNeopixelClear}
              className="btn-danger w-full mt-4"
              disabled={loading === 'neopixel-clear'}
            >
              Clear All
            </button>
          </div>
        </div>

        {/* LED Preview */}
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            LED Preview
          </h4>
          <div className="flex gap-2 justify-center">
            {hardwareData?.neopixel.colors.map((led, index) => (
              <div
                key={index}
                className="w-8 h-8 rounded-full border-2 border-gray-200 dark:border-gray-600 transition-all duration-300"
                style={{
                  backgroundColor: led.color,
                  boxShadow:
                    led.color !== '#000000' ? `0 0 10px ${led.color}` : 'none',
                }}
                title={`LED ${index + 1}: ${led.color}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
