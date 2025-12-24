/**
 * WebSocket Hook
 *
 * React hook for WebSocket connection management.
 */

import { useEffect, useCallback } from 'react';
import { websocketService } from '../services/websocket';
import { useStore } from './useStore';
import { HardwareData, SystemMetrics, WebSocketMessage } from '../types';

export function useWebSocket() {
  const { setConnected, setHardwareData, setSystemMetrics, addAlert } = useStore();

  const handleMessage = useCallback(
    (message: WebSocketMessage) => {
      switch (message.type) {
        case 'connected':
          console.log('WebSocket authenticated:', message.client_id);
          break;

        case 'hardware_update':
          if (message.data) {
            setHardwareData(message.data as HardwareData);
          }
          break;

        case 'system_update':
          if (message.data) {
            const metrics = message.data as SystemMetrics;
            setSystemMetrics(metrics);

            // Check for warnings
            if (metrics.cpu.temperature && metrics.cpu.temperature > 70) {
              addAlert('warning', `High CPU temperature: ${metrics.cpu.temperature.toFixed(1)}°C`);
            }
            if (metrics.memory.percent > 90) {
              addAlert('warning', `High memory usage: ${metrics.memory.percent.toFixed(1)}%`);
            }
          }
          break;

        case 'log_update':
          // Handle log updates if needed
          break;

        case 'subscribed':
          console.log('Subscribed to topics:', message.topics);
          break;

        case 'pong':
          // Heartbeat response
          break;

        default:
          console.log('Unknown message type:', message.type);
      }
    },
    [setHardwareData, setSystemMetrics, addAlert]
  );

  useEffect(() => {
    // Setup handlers
    const unsubMessage = websocketService.onMessage(handleMessage);
    const unsubConnect = websocketService.onConnect(() => setConnected(true));
    const unsubDisconnect = websocketService.onDisconnect(() => setConnected(false));

    // Connect
    websocketService.connect();

    // Cleanup
    return () => {
      unsubMessage();
      unsubConnect();
      unsubDisconnect();
    };
  }, [handleMessage, setConnected]);

  return {
    isConnected: websocketService.isConnected,
    send: websocketService.send.bind(websocketService),
    subscribe: websocketService.subscribe.bind(websocketService),
    unsubscribe: websocketService.unsubscribe.bind(websocketService),
  };
}
