import { useState, useEffect, useRef, useCallback } from 'react';

interface WebSocketHook {
  isConnected: boolean;
  lastMessage: any;
  sendMessage: (msg: any) => void;
}

export function useWebSocket(url: string | null): WebSocketHook {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (!url) return;

    if (ws.current) {
      ws.current.close();
    }

    const socket = new WebSocket(url);

    socket.onopen = () => {
      console.log(`Connected to WS: ${url}`);
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (err) {
        console.error('Error parsing WS message', err);
      }
    };

    socket.onclose = () => {
      console.log(`Disconnected from WS: ${url}`);
      setIsConnected(false);

      // Reconnect logic with exponential backoff
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
      reconnectTimeout.current = setTimeout(() => {
        reconnectAttempts.current += 1;
        connect();
      }, delay);
    };

    socket.onerror = (error) => {
      console.error('WS Error:', error);
      socket.close();
    };

    ws.current = socket;
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((msg: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg));
    }
  }, []);

  return { isConnected, lastMessage, sendMessage };
}
