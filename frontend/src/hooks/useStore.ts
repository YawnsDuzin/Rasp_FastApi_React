/**
 * Global State Store using Zustand
 *
 * Manages application state with minimal re-renders.
 */

import { create } from 'zustand';
import { HardwareData, SystemMetrics, AppConfig } from '../types';

interface StoreState {
  // Connection state
  isConnected: boolean;
  setConnected: (connected: boolean) => void;

  // Hardware data
  hardwareData: HardwareData | null;
  setHardwareData: (data: HardwareData) => void;

  // System metrics
  systemMetrics: SystemMetrics | null;
  setSystemMetrics: (metrics: SystemMetrics) => void;

  // App config
  config: AppConfig | null;
  setConfig: (config: AppConfig) => void;

  // UI state
  darkMode: boolean;
  toggleDarkMode: () => void;

  // Sidebar state
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // Active page
  activePage: string;
  setActivePage: (page: string) => void;

  // Temperature history for charts
  temperatureHistory: Array<{ time: string; value: number }>;
  addTemperaturePoint: (value: number) => void;

  // Humidity history for charts
  humidityHistory: Array<{ time: string; value: number }>;
  addHumidityPoint: (value: number) => void;

  // Notifications/Alerts
  alerts: Array<{ id: string; type: string; message: string; timestamp: Date }>;
  addAlert: (type: string, message: string) => void;
  removeAlert: (id: string) => void;
  clearAlerts: () => void;
}

const MAX_HISTORY_POINTS = 60; // Keep 60 data points

export const useStore = create<StoreState>((set, get) => ({
  // Connection state
  isConnected: false,
  setConnected: (connected) => set({ isConnected: connected }),

  // Hardware data
  hardwareData: null,
  setHardwareData: (data) => {
    set({ hardwareData: data });

    // Update temperature history
    if (data.sensors.temperature !== null) {
      get().addTemperaturePoint(data.sensors.temperature);
    }

    // Update humidity history
    if (data.sensors.humidity !== null) {
      get().addHumidityPoint(data.sensors.humidity);
    }
  },

  // System metrics
  systemMetrics: null,
  setSystemMetrics: (metrics) => set({ systemMetrics: metrics }),

  // App config
  config: null,
  setConfig: (config) => set({ config }),

  // UI state
  darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
  toggleDarkMode: () =>
    set((state) => {
      const newDarkMode = !state.darkMode;
      if (newDarkMode) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return { darkMode: newDarkMode };
    }),

  // Sidebar state
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  // Active page
  activePage: 'dashboard',
  setActivePage: (page) => set({ activePage: page }),

  // Temperature history
  temperatureHistory: [],
  addTemperaturePoint: (value) =>
    set((state) => {
      const now = new Date();
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      const newHistory = [...state.temperatureHistory, { time, value }];
      if (newHistory.length > MAX_HISTORY_POINTS) {
        newHistory.shift();
      }

      return { temperatureHistory: newHistory };
    }),

  // Humidity history
  humidityHistory: [],
  addHumidityPoint: (value) =>
    set((state) => {
      const now = new Date();
      const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });

      const newHistory = [...state.humidityHistory, { time, value }];
      if (newHistory.length > MAX_HISTORY_POINTS) {
        newHistory.shift();
      }

      return { humidityHistory: newHistory };
    }),

  // Alerts
  alerts: [],
  addAlert: (type, message) =>
    set((state) => {
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      const newAlert = { id, type, message, timestamp: new Date() };
      return { alerts: [...state.alerts, newAlert].slice(-10) }; // Keep last 10 alerts
    }),
  removeAlert: (id) =>
    set((state) => ({
      alerts: state.alerts.filter((a) => a.id !== id),
    })),
  clearAlerts: () => set({ alerts: [] }),
}));

// Initialize dark mode on load
if (typeof window !== 'undefined') {
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
  }
}
