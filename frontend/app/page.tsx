"use client";

import React, { useEffect } from 'react';
import MarketSelector from '../components/MarketSelector';
import StatsBar from '../components/StatsBar';
import OrderbookHeatmap from '../components/OrderbookHeatmap';
import ImbalanceChart from '../components/ImbalanceChart';
import { useWebSocket } from '../hooks/useWebSocket';
import { useStore } from '../lib/store';

export default function Dashboard() {
  const currentSymbol = useStore((state) => state.currentSymbol);
  const setSnapshot = useStore((state) => state.setSnapshot);

  // Actually, for consistency with how Next.js dev server works with a proxy:
  // Usually we'd use a relative URL but WebSocket needs absolute.
  // Assuming API is at port 8000 and frontend at 3000 as per docker-compose (common setup).
  // But let's use a more robust way:
  const getWsUrl = () => {
    if (!currentSymbol) return null;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    // In many dev setups, the WS might be on a different port than the frontend
    // If NEXT_PUBLIC_API_URL is set, we use that as the base.
    if (process.env.NEXT_PUBLIC_API_URL) {
      return process.env.NEXT_PUBLIC_API_URL.replace('http', 'ws') + `/ws/live/${currentSymbol}`;
    }
    // Fallback to current host on port 8000 (typical for this project's API)
    return `${protocol}//${host}:8000/ws/live/${currentSymbol}`;
  };

  const { lastMessage, isConnected } = useWebSocket(getWsUrl());

  useEffect(() => {
    if (lastMessage) {
      setSnapshot(lastMessage);
    }
  }, [lastMessage, setSnapshot]);

  return (
    <div className="min-h-screen bg-[#0A0A0F] text-white flex flex-col">
      <header className="border-b border-gray-800 bg-[#111] py-4 px-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-[#1A73E8] rounded flex items-center justify-center font-bold">P</div>
          <h1 className="text-xl font-bold tracking-tight">PacifiScope</h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} animate-pulse`} />
            <span className="text-xs text-gray-400 font-mono uppercase">{isConnected ? 'Live' : 'Disconnected'}</span>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col max-w-[1400px] mx-auto w-full p-4 gap-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="w-full md:w-64 shrink-0">
            <MarketSelector />
          </div>
          <div className="flex-1">
            <StatsBar />
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 flex flex-col gap-4">
            <div className="hidden md:block">
              <OrderbookHeatmap />
            </div>
            <ImbalanceChart />
          </div>
          <div className="md:col-span-1 space-y-4">
            <div className="bg-[#111] border border-gray-800 rounded-lg p-4 h-full">
              <h3 className="text-xs text-gray-400 font-mono mb-4 uppercase tracking-wider">Market Analysis</h3>
              <div className="space-y-6">
                <p className="text-sm text-gray-300 leading-relaxed">
                  Real-time orderbook footprint analysis for <span className="text-[#1A73E8] font-bold">{currentSymbol}</span>.
                  The heatmap above shows the concentration of liquidity at various price levels.
                  Darker intensities represent higher volume at that level.
                </p>

                <div className="p-3 bg-[#1A1A1F] border border-gray-700 rounded text-xs font-mono">
                  <div className="flex justify-between mb-1">
                    <span className="text-gray-500">Status:</span>
                    <span className={isConnected ? 'text-green-500' : 'text-red-500'}>{isConnected ? 'Active' : 'Offline'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Last Message:</span>
                    <span className="text-gray-300">{lastMessage?.ts ? new Date(lastMessage.ts).toLocaleTimeString() : 'N/A'}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-800">
                  <h4 className="text-[10px] text-gray-500 font-bold uppercase mb-2">Legend</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 opacity-80" />
                      <span className="text-xs text-gray-400">Bid Liquidity</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 opacity-80" />
                      <span className="text-xs text-gray-400">Ask Liquidity</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 border-t border-white border-dashed" />
                      <span className="text-xs text-gray-400">Mid Price</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <footer className="border-t border-gray-800 bg-[#0A0A0F] py-3 px-6 text-center">
        <p className="text-[10px] text-gray-600 font-mono">PACIFISCOPE — REAL-TIME LIQUIDITY INTELLIGENCE</p>
      </footer>
    </div>
  );
}
