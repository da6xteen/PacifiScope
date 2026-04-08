import React from 'react';
import useSWR from 'swr';
import { useStore } from '../lib/store';
import SignalSkeleton from './skeletons/SignalSkeleton';

interface Signal {
  direction: 'LONG' | 'SHORT';
  time: string;
  confidence: number;
  rules_fired: string[];
}

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export default function SignalFeed() {
  const currentSymbol = useStore((state) => state.currentSymbol);

  const { data: signals, error } = useSWR<Signal[]>(
    currentSymbol ? `/api/signals?symbol=${currentSymbol}&min_confidence=30` : null,
    fetcher,
    { refreshInterval: 30000 } // Refresh every 30s
  );

  if (error) return <div className="text-red-500 text-xs p-4">Failed to load signals</div>;
  if (!signals) return <SignalSkeleton />;

  return (
    <div className="bg-[#111] border border-gray-800 rounded-lg overflow-hidden">
      <div className="px-4 py-2 border-b border-gray-800 flex justify-between items-center">
        <h3 className="text-xs text-gray-400 font-mono uppercase tracking-wider">Alpha Signals</h3>
        <span className="text-[10px] text-[#1A73E8] font-mono">LIVE SCAN</span>
      </div>

      <div className="max-h-[300px] overflow-y-auto">
        {signals.length === 0 ? (
          <div className="p-8 text-center">
            <p className="text-xs text-gray-600 font-mono italic">No active patterns detected</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-900">
            {signals.map((signal: Signal, idx: number) => (
              <div key={idx} className="p-3 hover:bg-[#16161a] transition-colors">
                <div className="flex justify-between items-start mb-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-bold ${signal.direction === 'LONG' ? 'text-green-500' : 'text-red-500'}`}>
                      {signal.direction}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      {new Date(signal.time).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className={`px-1.5 py-0.5 rounded text-[10px] font-bold border ${
                    signal.confidence >= 66
                      ? 'bg-blue-900/30 text-blue-400 border-blue-800'
                      : 'bg-gray-800 text-gray-400 border-gray-700'
                  }`}>
                    {Math.round(signal.confidence)}% CONF
                  </div>
                </div>

                <div className="flex flex-wrap gap-1 mt-2">
                  {signal.rules_fired.map((rule: string) => (
                    <span key={rule} className="text-[9px] bg-gray-900 text-gray-400 px-1 rounded font-mono">
                      {rule}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-2 border-t border-gray-800 bg-[#0A0A0F]">
        <p className="text-[9px] text-gray-600 leading-tight">
          Signals expire after 5m of inactivity. Pure imbalance/whale pattern matching.
        </p>
      </div>
    </div>
  );
}
