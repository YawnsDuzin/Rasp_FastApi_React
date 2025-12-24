/**
 * Main Application Component
 */

import { useEffect } from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './hooks/useStore';
import { systemApi } from './services/api';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Hardware from './pages/Hardware';
import Sensors from './pages/Sensors';
import System from './pages/System';
import Logs from './pages/Logs';
import Settings from './pages/Settings';

function App() {
  const { activePage, setConfig } = useStore();

  // Initialize WebSocket connection
  useWebSocket();

  // Fetch config on mount
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const config = await systemApi.getConfig();
        setConfig(config as never);
      } catch (error) {
        console.error('Failed to fetch config:', error);
      }
    };

    fetchConfig();
  }, [setConfig]);

  // Render active page
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />;
      case 'hardware':
        return <Hardware />;
      case 'sensors':
        return <Sensors />;
      case 'system':
        return <System />;
      case 'logs':
        return <Logs />;
      case 'settings':
        return <Settings />;
      default:
        return <Dashboard />;
    }
  };

  return <Layout>{renderPage()}</Layout>;
}

export default App;
