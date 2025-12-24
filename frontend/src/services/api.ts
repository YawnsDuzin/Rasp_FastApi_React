/**
 * API Service
 *
 * Handles all REST API calls to the backend.
 */

const API_BASE = '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || errorData.message || 'API request failed'
    );
  }

  return response.json();
}

// Hardware API
export const hardwareApi = {
  getStatus: () => fetchApi<Record<string, unknown>>('/hardware/status'),

  getData: () => fetchApi<Record<string, unknown>>('/hardware/data'),

  // GPIO
  getGpioStatus: () => fetchApi<Record<string, unknown>>('/hardware/gpio'),

  setLed: (index: number, state: boolean) =>
    fetchApi<{ success: boolean }>('/hardware/gpio/led', {
      method: 'POST',
      body: JSON.stringify({ index, state }),
    }),

  setAllLeds: (state: boolean) =>
    fetchApi<{ success: boolean }>(`/hardware/gpio/led/all?state=${state}`, {
      method: 'POST',
    }),

  setRelay: (index: number, state: boolean) =>
    fetchApi<{ success: boolean }>('/hardware/gpio/relay', {
      method: 'POST',
      body: JSON.stringify({ index, state }),
    }),

  // PWM
  getPwmStatus: () => fetchApi<Record<string, unknown>>('/hardware/pwm'),

  setMotorSpeed: (speed: number) =>
    fetchApi<{ success: boolean }>('/hardware/pwm/motor', {
      method: 'POST',
      body: JSON.stringify({ speed }),
    }),

  setServoAngle: (angle: number) =>
    fetchApi<{ success: boolean }>('/hardware/pwm/servo', {
      method: 'POST',
      body: JSON.stringify({ angle }),
    }),

  // Sensors
  getSensors: () => fetchApi<Record<string, unknown>>('/hardware/sensors'),

  getDht: () => fetchApi<{ temperature: number; humidity: number }>('/hardware/sensors/dht'),

  getDistance: () => fetchApi<{ distance: number }>('/hardware/sensors/distance'),

  // I2C
  getI2cDevices: () => fetchApi<Record<string, unknown>>('/hardware/i2c/devices'),

  scanI2c: () => fetchApi<number[]>('/hardware/i2c/scan'),

  getBmp280: () => fetchApi<Record<string, number>>('/hardware/i2c/bmp280'),

  getAdc: () => fetchApi<Record<number, number>>('/hardware/i2c/adc'),

  // SPI
  getMcp3008: () => fetchApi<Record<number, number>>('/hardware/spi/mcp3008'),

  // Display
  getLcdInfo: () => fetchApi<Record<string, unknown>>('/hardware/display/lcd'),

  writeLcd: (text: string, row: number = 0, col: number = 0) =>
    fetchApi<{ success: boolean }>('/hardware/display/lcd/write', {
      method: 'POST',
      body: JSON.stringify({ text, row, col }),
    }),

  clearLcd: () =>
    fetchApi<{ success: boolean }>('/hardware/display/lcd/clear', {
      method: 'POST',
    }),

  // NeoPixel
  getNeopixelStatus: () => fetchApi<Record<string, unknown>>('/hardware/neopixel'),

  setNeopixelColor: (index: number | null, color: string) =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/color', {
      method: 'POST',
      body: JSON.stringify({ index, color }),
    }),

  startNeopixelEffect: (effect: string, speed: number = 0.05) =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/effect', {
      method: 'POST',
      body: JSON.stringify({ effect, speed }),
    }),

  stopNeopixelEffect: () =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/stop', {
      method: 'POST',
    }),

  clearNeopixel: () =>
    fetchApi<{ success: boolean }>('/hardware/neopixel/clear', {
      method: 'POST',
    }),

  // Simulation
  setSimulationValues: (values: Record<string, unknown>) =>
    fetchApi<{ success: boolean }>('/hardware/simulation/values', {
      method: 'POST',
      body: JSON.stringify(values),
    }),

  simulateButtonPress: (index: number) =>
    fetchApi<{ success: boolean }>(`/hardware/simulation/button/${index}`, {
      method: 'POST',
    }),
};

// System API
export const systemApi = {
  getMetrics: () => fetchApi<Record<string, unknown>>('/system/metrics'),

  getSummary: () => fetchApi<Record<string, unknown>>('/system/summary'),

  getHealth: () => fetchApi<Record<string, unknown>>('/system/health'),

  getPlatform: () => fetchApi<Record<string, unknown>>('/system/platform'),

  getProcess: () => fetchApi<Record<string, unknown>>('/system/process'),

  getConfig: () => fetchApi<Record<string, unknown>>('/system/config'),
};

// Data API
export const dataApi = {
  getSensorHistory: (sensorType: string = 'all', hours: number = 24, limit: number = 1000) =>
    fetchApi<Record<string, unknown>[]>(
      `/data/sensors?sensor_type=${sensorType}&hours=${hours}&limit=${limit}`
    ),

  getTemperatureTrend: (hours: number = 24) =>
    fetchApi<Array<{ timestamp: string; value: number }>>(
      `/data/temperature?hours=${hours}`
    ),

  getSystemLogs: (level?: string, hours: number = 24, limit: number = 100) => {
    let url = `/data/logs?hours=${hours}&limit=${limit}`;
    if (level) url += `&level=${level}`;
    return fetchApi<Record<string, unknown>[]>(url);
  },

  getDeviceHistory: (deviceType?: string, deviceId?: string, hours: number = 24) => {
    let url = `/data/devices?hours=${hours}`;
    if (deviceType) url += `&device_type=${deviceType}`;
    if (deviceId) url += `&device_id=${deviceId}`;
    return fetchApi<Record<string, unknown>[]>(url);
  },

  getStatistics: (hours: number = 24) =>
    fetchApi<Record<string, unknown>>(`/data/statistics?hours=${hours}`),

  cleanupData: (retentionDays: number = 30) =>
    fetchApi<{ success: boolean; deleted_records: number }>(
      `/data/cleanup?retention_days=${retentionDays}`,
      { method: 'POST' }
    ),
};

// WebSocket API
export const wsApi = {
  getStatus: () => fetchApi<Record<string, unknown>>('/ws/status'),

  getClients: () => fetchApi<Record<string, unknown>>('/ws/clients'),
};

export { ApiError };
