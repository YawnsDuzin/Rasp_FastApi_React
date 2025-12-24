/**
 * Layout Component
 *
 * Main application layout with sidebar and header.
 */

import { ReactNode } from 'react';
import { useStore } from '../hooks/useStore';
import {
  LayoutDashboard,
  Cpu,
  Thermometer,
  Activity,
  FileText,
  Settings,
  Menu,
  Moon,
  Sun,
  Wifi,
  WifiOff,
} from 'lucide-react';
import clsx from 'clsx';

interface LayoutProps {
  children: ReactNode;
}

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'hardware', label: 'Hardware', icon: Cpu },
  { id: 'sensors', label: 'Sensors', icon: Thermometer },
  { id: 'system', label: 'System', icon: Activity },
  { id: 'logs', label: 'Logs', icon: FileText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export default function Layout({ children }: LayoutProps) {
  const {
    sidebarOpen,
    toggleSidebar,
    darkMode,
    toggleDarkMode,
    activePage,
    setActivePage,
    isConnected,
    config,
  } = useStore();

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 flex flex-col bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 transition-all duration-300',
          sidebarOpen ? 'w-64' : 'w-20'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-center border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-500 rounded-lg flex items-center justify-center">
              <Cpu className="w-6 h-6 text-white" />
            </div>
            {sidebarOpen && (
              <div className="flex flex-col">
                <span className="font-bold text-gray-900 dark:text-white">RasPi HMI</span>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {config?.simulation_mode ? 'Simulation' : 'Hardware'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activePage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActivePage(item.id)}
                className={clsx(
                  'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-500 text-white'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="font-medium">{item.label}</span>}
              </button>
            );
          })}
        </nav>

        {/* Connection Status */}
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <div
            className={clsx(
              'flex items-center gap-3 px-4 py-2 rounded-lg',
              isConnected
                ? 'bg-green-100 dark:bg-green-900/30'
                : 'bg-red-100 dark:bg-red-900/30'
            )}
          >
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-600 dark:text-green-400" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-600 dark:text-red-400" />
            )}
            {sidebarOpen && (
              <span
                className={clsx(
                  'text-sm font-medium',
                  isConnected
                    ? 'text-green-700 dark:text-green-400'
                    : 'text-red-700 dark:text-red-400'
                )}
              >
                {isConnected ? 'Connected' : 'Disconnected'}
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div
        className={clsx(
          'flex-1 flex flex-col transition-all duration-300',
          sidebarOpen ? 'ml-64' : 'ml-20'
        )}
      >
        {/* Header */}
        <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <Menu className="w-5 h-5 text-gray-600 dark:text-gray-300" />
            </button>
            <h1 className="text-xl font-semibold text-gray-900 dark:text-white capitalize">
              {activePage}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Real-time indicator */}
            <div className="flex items-center gap-2">
              <div className={clsx(
                'status-indicator',
                isConnected ? 'online' : 'offline'
              )} />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                Real-time
              </span>
            </div>

            {/* Dark mode toggle */}
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              {darkMode ? (
                <Sun className="w-5 h-5 text-yellow-500" />
              ) : (
                <Moon className="w-5 h-5 text-gray-600" />
              )}
            </button>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
