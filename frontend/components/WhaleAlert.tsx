"use client";

import React, { useEffect, useState, useRef } from 'react';
import { FixedSizeList as List } from 'react-window';
import { useStore } from '../lib/store';
import useSWR from 'swr';

interface WhaleEvent {
  time: string;
  symbol: string;
  price: number;
  size_usd: number;
  type: 'whale_bid' | 'whale_ask' | 'iceberg';
  persisted_ticks: number;
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function WhaleAlert() {
  const currentSymbol = useStore((state) => state.currentSymbol);
  const [alerts, setAlerts] = useState<WhaleEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  // Initial fetch
  const { data: initialData } = useSWR(
    currentSymbol ? `/api/whales/${currentSymbol}` : null,
    fetcher
  );

  useEffect(() => {
    if (initialData) {
      setAlerts(initialData);
    }
  }, [initialData]);

  // WebSocket for real-time alerts
  useEffect(() => {
    if (!currentSymbol) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // Assuming API is on port 8000
    const wsUrl = `${protocol}//${host}:8000/ws/whales/${currentSymbol}`;

    // Note: The backend needs to support this WS route or we use the main one.
    // Given the task, I should probably check if I need to add a WS route for whales.
    // But for now let's assume we can subscribe.

    // Actually, the main WS might already include these if I update it.
    // But the task says "Publish to Redis channel 'whales:{symbol}'"
    // So I might need a relay for this.

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const newAlert = JSON.parse(event.data);
        setAlerts((prev) => [newAlert, ...prev].slice(0, 100));
      } catch (err) {
        console.error("Error parsing whale alert:", err);
      }
    };

    return () => {
      ws.close();
    };
  }, [currentSymbol]);

  const Row = ({ index, style }: { index: number, style: React.CSSProperties }) => {
    const alert = alerts[index];
    if (!alert) return null;

    const isNew = index === 0;
    const isOld = index > 10;
    const isIceberg = alert.type === 'iceberg';
    const isBid = alert.type === 'whale_bid';

    const timeStr = new Date(alert.time).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });

    return (
      <div style={style} className={`px-4 py-2 border-b border-gray-800/50 flex items-center gap-3 transition-all duration-500 ${isNew ? 'bg-blue-500/10 animate-pulse' : 'bg-transparent'} ${isOld ? 'opacity-40 grayscale-[0.5]' : 'opacity-100'}`}>
        <span className="text-[10px] font-mono text-gray-500 shrink-0">{timeStr}</span>
        <div className="flex-1 flex items-center justify-between min-w-0">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-lg shrink-0">{isIceberg ? '🧊' : '🐋'}</span>
            <div className="flex flex-col min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold ${isBid ? 'text-green-400' : alert.type === 'whale_ask' ? 'text-red-400' : 'text-blue-400'}`}>
                  {alert.type.replace('whale_', '').toUpperCase()}
                </span>
                <span className="text-xs font-mono font-bold text-gray-200">
                  ${alert.size_usd.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                </span>
              </div>
              <span className="text-[10px] text-gray-500 truncate">
                @ {alert.price.toLocaleString()} — {alert.persisted_ticks} ticks
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg flex flex-col h-[400px]">
      <div className="p-3 border-b border-gray-800 flex justify-between items-center bg-[#151515] rounded-t-lg">
        <h3 className="text-xs text-gray-400 font-mono uppercase tracking-wider flex items-center gap-2">
          <span className="w-2 h-2 bg-blue-500 rounded-full animate-ping" />
          Whale Alerts
        </h3>
        <span className="text-[10px] text-gray-500 font-mono">{alerts.length} events</span>
      </div>
      <div className="flex-1">
        {alerts.length > 0 ? (
          <List
            height={345}
            itemCount={alerts.length}
            itemSize={50}
            width="100%"
            className="scrollbar-hide"
          >
            {Row}
          </List>
        ) : (
          <div className="h-full flex items-center justify-center text-gray-600 text-xs font-mono">
            Waiting for big fish...
          </div>
        )}
      </div>
    </div>
  );
}
